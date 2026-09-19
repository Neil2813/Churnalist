"""Full article translation service with persistent database caching."""
from __future__ import annotations

import datetime
from typing import Any
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import LANGUAGE_NAMES, SUPPORTED_LANGUAGES
from app.core.exceptions import ArticleNotFoundError, TranslationError, UnsupportedLanguageError
from app.core.logging import get_logger
from app.db.models.article import Article, ArticleTranslation
from app.llm.client import GroqClient
from app.llm.prompts import FULL_ARTICLE_TRANSLATION_PROMPT
from app.schemas.articles import ArticleTranslationResponse

logger = get_logger(__name__)

# Max characters to send to LLM in one translation call for rate/cost control
MAX_TRANSLATION_CHARS = 16000


class ArticleTranslationSchema(BaseModel):
    """Structured LLM response schema for article translation."""
    translated_title: str | None = None
    translated_content: str


class TranslationService:
    """Service handling full-article translation and caching."""

    def __init__(self, llm_client: GroqClient | None = None) -> None:
        self.llm_client = llm_client

    def _get_llm_client(self) -> GroqClient | None:
        if self.llm_client is not None:
            return self.llm_client
        settings = get_settings()
        if settings.groq_api_key:
            self.llm_client = GroqClient(
                api_key=settings.groq_api_key,
                default_model=settings.groq_model,
                fast_model=settings.groq_fast_model,
                timeout=settings.llm_timeout_seconds,
                max_concurrent=settings.max_concurrent_llm_calls,
            )
        return self.llm_client

    async def get_or_translate_article(
        self,
        db: AsyncSession,
        article_id: str,
        target_language: str,
        title_only: bool = False,
    ) -> ArticleTranslationResponse:
        """
        Fetch cached translation from DB, or translate article via LLM and cache it.
        When title_only=True, performs a lightweight translation for headline rendering.
        """
        target_lang = target_language.lower().strip()
        if not target_lang or target_lang not in SUPPORTED_LANGUAGES:
            supported_str = ", ".join(sorted(SUPPORTED_LANGUAGES))
            raise UnsupportedLanguageError(
                f"Unsupported language '{target_language}'. Supported languages: {supported_str}"
            )

        # 1. Fetch article from DB
        stmt = select(Article).where(Article.id == article_id)
        res = await db.execute(stmt)
        article = res.scalar_one_or_none()
        if not article:
            raise ArticleNotFoundError(f"Article with ID '{article_id}' was not found.")

        orig_lang = (article.language or "en").lower()
        orig_lang_name = LANGUAGE_NAMES.get(orig_lang, orig_lang.upper())
        target_lang_name = LANGUAGE_NAMES.get(target_lang, target_lang.upper())

        # 2. If target language matches original language, return original directly
        if target_lang == orig_lang:
            return ArticleTranslationResponse(
                article_id=article.id,
                target_language=target_lang,
                target_language_name=target_lang_name,
                translated_title=article.title,
                translated_content=article.content or "",
                original_language=orig_lang,
                original_language_name=orig_lang_name,
                original_title=article.title,
                original_content=article.content,
                cached=True,
                created_at=article.retrieved_at or article.created_at or datetime.datetime.now(datetime.timezone.utc),
            )

        # 3. Check translation cache table
        trans_stmt = select(ArticleTranslation).where(
            ArticleTranslation.article_id == article.id,
            ArticleTranslation.target_language == target_lang,
        )
        trans_res = await db.execute(trans_stmt)
        cached_trans = trans_res.scalar_one_or_none()

        if cached_trans:
            if title_only and cached_trans.translated_title:
                logger.info("translation_cache_hit_title_only", article_id=article.id, target_lang=target_lang)
                return ArticleTranslationResponse(
                    article_id=article.id,
                    target_language=cached_trans.target_language,
                    target_language_name=target_lang_name,
                    translated_title=cached_trans.translated_title,
                    translated_content=cached_trans.translated_content or "",
                    original_language=orig_lang,
                    original_language_name=orig_lang_name,
                    original_title=article.title,
                    original_content=article.content,
                    cached=True,
                    created_at=cached_trans.created_at or datetime.datetime.now(datetime.timezone.utc),
                )
            elif not title_only and (bool(cached_trans.translated_content and (len(cached_trans.translated_content) > 400 or len(article.content or "") <= 400)) or not bool(article.content and article.content.strip())):
                logger.info("translation_cache_hit", article_id=article.id, target_lang=target_lang)
                return ArticleTranslationResponse(
                    article_id=article.id,
                    target_language=cached_trans.target_language,
                    target_language_name=target_lang_name,
                    translated_title=cached_trans.translated_title,
                    translated_content=cached_trans.translated_content or "",
                    original_language=orig_lang,
                    original_language_name=orig_lang_name,
                    original_title=article.title,
                    original_content=article.content,
                    cached=True,
                    created_at=cached_trans.created_at or datetime.datetime.now(datetime.timezone.utc),
                )

        # 4. Not cached: Translate with LLM
        title_to_translate = article.title or ""
        has_original_content = bool(article.content and article.content.strip())
        if title_only:
            content_to_translate = (article.content or "").strip()[:350] or "[Translate headline/title only]"
        else:
            content_to_translate = (article.content or "")[:MAX_TRANSLATION_CHARS]

        client = self._get_llm_client()
        if not client or not client.api_key:
            logger.error(
                "translation_client_unavailable",
                article_id=article.id,
                target_lang=target_lang,
            )
            raise TranslationError("Translation failed: LLM service is not configured or missing API key.")

        user_prompt = FULL_ARTICLE_TRANSLATION_PROMPT.format(
            title=title_to_translate,
            content=content_to_translate,
            target_language=target_lang,
            target_language_name=target_lang_name,
        )

        try:
            llm_output = await client.generate_structured(
                system_prompt="You are a professional news article translator. Translate the text faithfully.",
                user_prompt=user_prompt,
                response_schema=ArticleTranslationSchema,
                prompt_version="full_article_v1",
            )
            translated_title = llm_output.translated_title or title_to_translate
            translated_content = (llm_output.translated_content or "")
        except Exception as e:
            logger.error(
                "translation_llm_failed",
                exc_info=True,
                error=str(e),
                article_id=article.id,
                target_lang=target_lang,
            )
            raise TranslationError(f"Translation failed: {e}")

        if not title_only and has_original_content and (not translated_content or not translated_content.strip()):
            logger.error(
                "translation_empty_response",
                article_id=article.id,
                target_lang=target_lang,
            )
            raise TranslationError("Translation failed: Model returned empty translation.")

        # 5. Save or update cache table
        if cached_trans:
            cached_trans.translated_title = translated_title
            if not title_only:
                cached_trans.translated_content = translated_content
            await db.commit()
            await db.refresh(cached_trans)
            target_trans = cached_trans
        else:
            new_trans = ArticleTranslation(
                article_id=article.id,
                target_language=target_lang,
                translated_title=translated_title,
                translated_content=translated_content,
            )
            db.add(new_trans)
            await db.commit()
            await db.refresh(new_trans)
            target_trans = new_trans

        logger.info("translation_cached", article_id=article.id, target_lang=target_lang, title_only=title_only)

        return ArticleTranslationResponse(
            article_id=article.id,
            target_language=target_trans.target_language,
            target_language_name=target_lang_name,
            translated_title=target_trans.translated_title,
            translated_content=target_trans.translated_content,
            original_language=orig_lang,
            original_language_name=orig_lang_name,
            original_title=article.title,
            original_content=article.content,
            cached=False,
            created_at=target_trans.created_at,
        )
