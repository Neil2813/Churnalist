"""Full article translation service with Google Translate free version and persistent database caching."""
from __future__ import annotations

import datetime
import httpx
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

# Max characters to send to translation in one call
MAX_TRANSLATION_CHARS = 16000
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
GOOGLE_TRANSLATE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


async def google_translate_free(
    text: str,
    target_lang: str,
    source_lang: str = "auto",
    http_client: httpx.AsyncClient | None = None,
) -> str:
    """
    Translates text using Google Translate free web endpoint with paragraph chunking.
    No API key required.
    """
    if not text or not text.strip():
        return ""

    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        close_client = True

    try:
        # Split text into chunks of <= 1500 chars to respect request bounds
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for line in text.splitlines(keepends=True):
            if current_len + len(line) > 1500 and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = [line]
                current_len = len(line)
            else:
                current_chunk.append(line)
                current_len += len(line)

        if current_chunk:
            chunks.append("".join(current_chunk))

        translated_parts: list[str] = []
        for chunk in chunks:
            if not chunk.strip():
                translated_parts.append(chunk)
                continue

            params = {
                "client": "dict-chrome-ex",
                "sl": source_lang,
                "tl": target_lang,
                "dt": "t",
                "q": chunk,
            }

            res = await http_client.get(
                GOOGLE_TRANSLATE_URL, params=params, headers=GOOGLE_TRANSLATE_HEADERS
            )
            if res.status_code == 200:
                data = res.json()
                translated_text = "".join(
                    part[0] for part in data[0] if part and len(part) > 0 and part[0]
                )
                translated_parts.append(translated_text)
            else:
                raise RuntimeError(f"Google Translate HTTP status {res.status_code}")

        return "".join(translated_parts)
    finally:
        if close_client:
            await http_client.aclose()


class ArticleTranslationSchema(BaseModel):
    """Structured LLM response schema for article translation fallback."""
    translated_title: str | None = None
    translated_content: str


class TranslationService:
    """Service handling full-article translation with free Google Translate and database caching."""

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
        Fetch cached translation from DB, or translate article via Google Translate (free)
        and cache it in SQLite DB.
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

        # 4. Perform translation
        title_to_translate = article.title or ""
        has_original_content = bool(article.content and article.content.strip())
        content_to_translate = (article.content or "")[:MAX_TRANSLATION_CHARS]

        translated_title = ""
        translated_content = ""

        # If a custom LLM client was explicitly passed in (e.g. in mock unit tests), use it
        if self.llm_client is not None:
            client = self._get_llm_client()
            user_prompt = FULL_ARTICLE_TRANSLATION_PROMPT.format(
                title=title_to_translate,
                content=(article.content or "")[:350] if title_only else content_to_translate,
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
                translated_content = llm_output.translated_content or ""
            except Exception as e:
                logger.error("translation_llm_failed", exc_info=True, error=str(e), article_id=article.id, target_lang=target_lang)
                raise TranslationError(f"Translation failed: {e}")
        else:
            # Primary production engine: Free Google Translate
            try:
                if title_to_translate:
                    translated_title = await google_translate_free(
                        title_to_translate, target_lang=target_lang, source_lang=orig_lang
                    )
                if not title_only and content_to_translate:
                    translated_content = await google_translate_free(
                        content_to_translate, target_lang=target_lang, source_lang=orig_lang
                    )
                logger.info("google_translate_free_success", article_id=article.id, target_lang=target_lang, title_only=title_only)
            except Exception as exc:
                logger.warning("google_translate_free_failed_falling_back_to_llm", error=str(exc))
                client = self._get_llm_client()
                if client and client.api_key:
                    user_prompt = FULL_ARTICLE_TRANSLATION_PROMPT.format(
                        title=title_to_translate,
                        content=(article.content or "")[:350] if title_only else content_to_translate,
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
                        translated_content = llm_output.translated_content or ""
                    except Exception as e:
                        raise TranslationError(f"Translation failed: {e}")
                else:
                    raise TranslationError(f"Google Translate failed and no LLM client configured: {exc}")

        if not title_only and has_original_content and not translated_content.strip():
            raise TranslationError("Translation failed: Result was empty.")

        # 5. Save or update DB cache
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
