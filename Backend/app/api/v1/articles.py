"""FastAPI routes for news article ingestion and management."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.deps import DBSession
from app.schemas.articles import ArticleDetailResponse, ArticleResponse, ArticleTranslationResponse
from app.schemas.ingestion import IngestRssRequest, IngestionJobResponse, IngestUrlRequest
from app.services.article_service import ArticleService
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/articles", tags=["Articles"])
service = ArticleService()
translation_service = TranslationService()


@router.post(
    "/ingest-url",
    response_model=ArticleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single news article by URL",
)
async def ingest_article_url(
    payload: IngestUrlRequest,
    db: DBSession,
) -> ArticleDetailResponse:
    """
    Fetch, clean, normalize, and store a news article by URL.
    Trigger content versioning if URL was previously fetched with modified text.
    """
    article = await service.ingest_url(db, payload)
    return ArticleDetailResponse.model_validate(article)


@router.post(
    "/ingest-rss",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger RSS/Atom feed ingestion batch job",
)
async def ingest_rss_feed(
    payload: IngestRssRequest,
    db: DBSession,
) -> IngestionJobResponse:
    """
    Fetch latest articles from an RSS feed, process HTML extraction,
    deduplicate against existing DB records, and record job metrics.
    """
    job = await service.ingest_rss(db, payload)
    return IngestionJobResponse.model_validate(job)


@router.get(
    "",
    response_model=list[ArticleResponse],
    summary="List ingested articles",
)
async def list_articles(
    db: DBSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    event_id: str | None = Query(default=None),
    language: str | None = Query(default=None),
) -> list[ArticleResponse]:
    """Retrieve a list of ingested articles with optional filters."""
    articles = await service.list_articles(
        db, skip=skip, limit=limit, event_id=event_id, language=language
    )
    return [ArticleResponse.model_validate(art) for art in articles]


@router.get(
    "/{article_id}",
    response_model=ArticleDetailResponse,
    summary="Get detailed article record by ID",
)
async def get_article_detail(
    article_id: str,
    db: DBSession,
) -> ArticleDetailResponse:
    """Get full content, metadata, and version snapshots for an article."""
    article = await service.get_article(db, article_id)
    return ArticleDetailResponse.model_validate(article)


@router.get(
    "/{article_id}/translate",
    response_model=ArticleTranslationResponse,
    summary="Translate full article content into a target language",
)
async def translate_article(
    article_id: str,
    db: DBSession,
    lang: str = Query(default="en", description="Target ISO language code, e.g. en, hi, ta, te, bn"),
    title_only: bool = Query(default=False, description="Translate only the headline for lightweight sidebar card rendering"),
) -> ArticleTranslationResponse:
    """
    Translate full news article title and content into the requested target language.
    Checks the database cache table first; calls Google Translate if not cached, then stores and returns the result.
    """
    return await translation_service.get_or_translate_article(
        db=db,
        article_id=article_id,
        target_language=lang,
        title_only=title_only,
    )


from pydantic import BaseModel

class TranslateTextPayload(BaseModel):
    text: str
    target_lang: str = "en"

class TranslateTextResponse(BaseModel):
    original_text: str
    translated_text: str
    target_lang: str


@router.post(
    "/translate-text",
    response_model=TranslateTextResponse,
    summary="Translate text snippet using free Google Translate",
)
async def translate_text(payload: TranslateTextPayload) -> TranslateTextResponse:
    """Translate arbitrary text snippet using free Google Translate engine."""
    from app.services.translation_service import google_translate_free
    translated = await google_translate_free(payload.text, target_lang=payload.target_lang)
    return TranslateTextResponse(
        original_text=payload.text,
        translated_text=translated or payload.text,
        target_lang=payload.target_lang,
    )

