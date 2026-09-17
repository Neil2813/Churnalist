"""Article high-level domain service."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.article import Article
from app.db.models.ingestion_job import IngestionJob
from app.db.repositories.article_repository import ArticleRepository
from app.ingestion.orchestrator import IngestionOrchestrator
from app.ingestion.providers.rss import RSSProvider
from app.schemas.ingestion import IngestRssRequest, IngestUrlRequest


class ArticleService:
    """High-level service for article ingestion and querying."""

    def __init__(self, orchestrator: IngestionOrchestrator | None = None):
        self.orchestrator = orchestrator or IngestionOrchestrator()

    async def ingest_url(self, db: AsyncSession, request: IngestUrlRequest) -> Article:
        """Ingest a single URL via IngestionOrchestrator."""
        article = await self.orchestrator.ingest_single_url(
            db=db,
            url=str(request.url),
            event_id=request.event_id,
            source_type=request.source_type,
        )
        # Reload with versions eagerly loaded so ArticleDetailResponse.model_validate works
        reloaded = await ArticleRepository.get_by_id(db, article.id)
        return reloaded or article

    async def ingest_rss(self, db: AsyncSession, request: IngestRssRequest) -> IngestionJob:
        """Trigger RSS feed batch ingestion."""
        provider = RSSProvider(str(request.rss_url))
        return await self.orchestrator.run_job(
            db=db,
            provider=provider,
            event_id=request.event_id,
            max_items=request.max_items,
        )

    async def get_article(self, db: AsyncSession, article_id: str) -> Article:
        """Get article by ID or raise NotFoundError."""
        article = await ArticleRepository.get_by_id(db, article_id)
        if not article:
            raise NotFoundError(f"Article with ID '{article_id}' was not found.")
        return article

    async def list_articles(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        event_id: str | None = None,
        language: str | None = None,
    ) -> Sequence[Article]:
        """List articles with pagination."""
        return await ArticleRepository.list_articles(
            db=db,
            skip=skip,
            limit=limit,
            event_id=event_id,
            language=language,
        )
