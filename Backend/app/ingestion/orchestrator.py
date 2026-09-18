"""Ingestion Orchestrator managing batch ingestion jobs, extraction, deduplication, and persistence."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ExtractionStatus, IngestionStatus, SourceType
from app.core.logging import get_logger
from app.db.models.article import Article, ArticleVersion
from app.db.models.ingestion_job import IngestionJob
from app.ingestion.article_extractor import ArticleExtractor
from app.ingestion.base import BaseProvider, RawDocument
from app.ingestion.deduplicator import DeduplicationAction, Deduplicator
from app.ingestion.normalizer import ArticleNormalizer

logger = get_logger(__name__)


class IngestionOrchestrator:
    """
    Coordinates the full news ingestion pipeline:
    Provider Fetch -> HTML Extraction -> Text Normalization -> Deduplication -> DB Persistence.
    """

    def __init__(self, extractor: ArticleExtractor | None = None):
        self.extractor = extractor or ArticleExtractor()

    async def run_job(
        self,
        db: AsyncSession,
        provider: BaseProvider,
        event_id: str | None = None,
        max_items: int = 20,
    ) -> IngestionJob:
        """Execute a full ingestion job for a specified provider."""
        # 1. Create IngestionJob DB record
        job = IngestionJob(
            provider=provider.provider_name,
            event_id=event_id,
            status=IngestionStatus.RUNNING,
            started_at=datetime.utcnow(),
            documents_found=0,
            documents_added=0,
            documents_skipped=0,
            documents_failed=0,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        try:
            logger.info("starting_ingestion_job", job_id=job.id, provider=job.provider)
            raw_docs = await provider.fetch_latest(limit=max_items)
            job.documents_found = len(raw_docs)

            for raw_doc in raw_docs:
                await self._process_raw_document(db, job, raw_doc, event_id)

            job.status = IngestionStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            logger.info(
                "ingestion_job_completed",
                job_id=job.id,
                added=job.documents_added,
                skipped=job.documents_skipped,
                failed=job.documents_failed,
            )
        except Exception as exc:
            logger.error("ingestion_job_failed", job_id=job.id, error=str(exc), exc_info=True)
            job.status = IngestionStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()

        job.metadata_json = json.dumps({
            "added": job.documents_added,
            "skipped": job.documents_skipped,
            "failed": job.documents_failed,
            "found": job.documents_found,
        })
        await db.commit()
        await db.refresh(job)
        return job

    async def ingest_single_url(
        self,
        db: AsyncSession,
        url: str,
        event_id: str | None = None,
        source_type: SourceType = SourceType.NEWSROOM,
    ) -> Article:
        """Ingest, parse, normalize, and store a single article by direct URL."""
        # Normalize target URL
        norm_url = ArticleNormalizer.normalize_article_url(url)

        # Extract full article content
        extracted = await self.extractor.extract_from_url(norm_url)

        # Normalize text and dates
        clean_text = ArticleNormalizer.normalize_text(extracted.text or "")
        pub_date = ArticleNormalizer.parse_published_date(extracted.published_date_str)
        lang, lang_conf = ArticleNormalizer.detect_language(clean_text)

        target_url = extracted.canonical_url or norm_url

        # Check deduplication & versioning
        dedup_res = await Deduplicator.evaluate(db, target_url, clean_text)

        if dedup_res.action == DeduplicationAction.SKIP_DUPLICATE:
            logger.info("article_skipped_exact_duplicate", url=target_url)
            return dedup_res.existing_article  # type: ignore

        if dedup_res.action == DeduplicationAction.NEW_VERSION and dedup_res.existing_article:
            existing = dedup_res.existing_article
            # Store snapshot of old version
            version_count = len(existing.versions) + 1 if existing.versions else 1
            version = ArticleVersion(
                article_id=existing.id,
                version_number=version_count,
                content=existing.content or "",
                content_hash=existing.content_hash or "",
                retrieved_at=existing.retrieved_at or datetime.utcnow(),
                change_type="CONTENT_UPDATE",
                change_summary="Re-fetched article with updated content.",
            )
            db.add(version)

            # Update existing article record
            existing.content = clean_text
            existing.content_hash = dedup_res.content_hash
            existing.retrieved_at = datetime.utcnow()
            if extracted.title:
                existing.title = extracted.title
            await db.commit()
            await db.refresh(existing)
            logger.info("article_updated_new_version", article_id=existing.id, version=version_count)
            return existing

        # Create new Article record
        new_article = Article(
            event_id=event_id,
            url=target_url,
            canonical_url=extracted.canonical_url,
            url_hash=dedup_res.url_hash,
            title=extracted.title or "Untitled Article",
            author=extracted.author,
            language=lang,
            language_confidence=lang_conf,
            content=clean_text,
            content_hash=dedup_res.content_hash,
            published_at=pub_date,
            retrieved_at=datetime.utcnow(),
            source_type=source_type.value if hasattr(source_type, "value") else str(source_type),
            extraction_status=ExtractionStatus.FULL.value if clean_text else ExtractionStatus.PARTIAL.value,
            metadata_json=json.dumps(extracted.metadata),
        )

        db.add(new_article)
        await db.commit()
        await db.refresh(new_article)
        logger.info("new_article_created", article_id=new_article.id, url=target_url)
        return new_article

    async def _process_raw_document(
        self,
        db: AsyncSession,
        job: IngestionJob,
        raw_doc: RawDocument,
        event_id: str | None = None,
    ) -> None:
        """Extract, normalize, deduplicate, and persist a RawDocument from a feed."""
        try:
            # If raw document has HTML or empty content, extract body text
            if raw_doc.raw_html and len(raw_doc.raw_html) > len(raw_doc.content or ""):
                extracted = self.extractor.extract_from_html(raw_doc.raw_html, raw_doc.url)
                clean_text = ArticleNormalizer.normalize_text(extracted.text or "")
                title = extracted.title or raw_doc.title
            else:
                clean_text = ArticleNormalizer.normalize_text(raw_doc.content or "")
                title = raw_doc.title

            norm_url = ArticleNormalizer.normalize_article_url(raw_doc.url)
            lang, lang_conf = ArticleNormalizer.detect_language(clean_text, default_lang=raw_doc.language)

            dedup_res = await Deduplicator.evaluate(db, norm_url, clean_text)

            if dedup_res.action == DeduplicationAction.SKIP_DUPLICATE:
                job.documents_skipped += 1
                return

            if dedup_res.action == DeduplicationAction.NEW_VERSION and dedup_res.existing_article:
                existing = dedup_res.existing_article
                version = ArticleVersion(
                    article_id=existing.id,
                    version_number=(len(existing.versions) + 1) if existing.versions else 1,
                    content=existing.content or "",
                    content_hash=existing.content_hash or "",
                    retrieved_at=existing.retrieved_at or datetime.utcnow(),
                    change_type="FEED_UPDATE",
                )
                db.add(version)
                existing.content = clean_text
                existing.content_hash = dedup_res.content_hash
                existing.retrieved_at = datetime.utcnow()
                job.documents_added += 1
                return

            # New Article
            article = Article(
                event_id=event_id or job.event_id,
                url=norm_url,
                url_hash=dedup_res.url_hash,
                title=title or "Untitled Feed Article",
                author=raw_doc.author,
                language=lang,
                language_confidence=lang_conf,
                content=clean_text,
                content_hash=dedup_res.content_hash,
                published_at=raw_doc.published_at,
                retrieved_at=datetime.utcnow(),
                source_type=raw_doc.source_type.value if hasattr(raw_doc.source_type, "value") else str(raw_doc.source_type),
                extraction_status=ExtractionStatus.FULL.value if clean_text else ExtractionStatus.PARTIAL.value,
                metadata_json=json.dumps(raw_doc.metadata),
            )
            db.add(article)
            job.documents_added += 1

        except Exception as exc:
            logger.warning("failed_processing_feed_document", url=raw_doc.url, error=str(exc))
            job.documents_failed += 1
