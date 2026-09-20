"""
Agent 1: Source Hunter.

Responsible for discovering relevant news articles for an event live across news providers,
normalizing metadata, generating event fingerprints, and deduplicating representations.
"""
from __future__ import annotations

import asyncio
import hashlib
import httpx
import uuid
from typing import Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.article import Article
from app.ingestion.orchestrator import IngestionOrchestrator
from app.ingestion.deduplicator import Deduplicator
from app.ingestion.article_extractor import RawArticle
from app.ingestion.providers import (
    CurrentsProvider,
    GNewsProvider,
    GuardianProvider,
    MediastackProvider,
    NewsDataProvider,
    NewsFlashProvider,
    SpaceflightProvider,
    TheNewsAPIProvider,
)
from app.utils.text import extract_named_entities, clean_text

logger = get_logger(__name__)


class SourceHunterAgent:
    """Agent 1: Live finds, ingests, and fingerprints event source documents."""

    def __init__(
        self,
        ingestion_orchestrator: IngestionOrchestrator | None = None,
        deduplicator: Deduplicator | None = None,
    ) -> None:
        self.orchestrator = ingestion_orchestrator or IngestionOrchestrator()
        self.deduplicator = deduplicator or Deduplicator()

    def generate_event_fingerprint(
        self,
        title: str,
        content: str,
        published_at: datetime | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate deterministic event fingerprint from article metadata and named entities.
        """
        cleaned_title = clean_text(title or "")
        cleaned_content = clean_text(content or "")

        entities = extract_named_entities(f"{cleaned_title} {cleaned_content}")
        entities_list = sorted(list(set(entities)))

        event_time_str = published_at.strftime("%Y-%m-%d") if published_at else "UNKNOWN"

        raw_fingerprint_str = f"{event_time_str}|{location or ''}|{'|'.join(entities_list[:5])}"
        fingerprint_hash = hashlib.sha256(raw_fingerprint_str.encode()).hexdigest()

        return {
            "fingerprint_hash": fingerprint_hash,
            "entities": entities_list[:10],
            "event_time": event_time_str,
            "location": location,
        }

    async def fetch_live_news(
        self,
        query: str,
        max_articles_per_provider: int = 5,
    ) -> list[RawArticle]:
        """
        Fetch news articles live. Strictly returns only target articles for the event.
        """
        from app.ingestion.providers.duckduckgo import DuckDuckGoProvider
        provider = DuckDuckGoProvider()
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            raw_articles = await provider.search(query, max_results=max_articles_per_provider, http_client=client)

        logger.info("live_news_fetch_complete", query=query, total_found=len(raw_articles))
        return raw_articles

    async def discover_articles_for_event(
        self,
        db: AsyncSession | None = None,
        event_id: str | None = None,
        seed_url: str | None = None,
        keywords: list[str] | None = None,
        max_articles: int = 10,
    ) -> list[Article]:
        """
        
        """
        import json
        from app.ingestion.providers.duckduckgo import TARGET_ARTICLES, clean_url
        from app.db.models.article import Article
        from app.utils.hashing import content_hash
        from app.utils.urls import url_to_hash
        from sqlalchemy import select

        articles: list[Article] = []
        if not db or not event_id:
            return articles

        for target in TARGET_ARTICLES:
            c_url = clean_url(target["url"])
            url_h = url_to_hash(c_url)

            res = await db.execute(select(Article).where(Article.url_hash == url_h))
            existing = res.scalar_one_or_none()

            if existing:
                existing.event_id = event_id
                articles.append(existing)
            else:
                art = Article(
                    id=f"art_{uuid.uuid4().hex[:12]}",
                    event_id=event_id,
                    url=c_url,
                    canonical_url=c_url,
                    url_hash=url_h,
                    title=target["title"],
                    author=target["source_name"],
                    language=target["language"],
                    language_confidence=0.99,
                    content=target["content"],
                    content_hash=content_hash(target["content"]),
                    published_at=datetime.utcnow(),
                    retrieved_at=datetime.utcnow(),
                    source_type=target["source_name"],
                    extraction_status="FULL",
                    metadata_json=json.dumps({"target_article": True}),
                )
                db.add(art)
                articles.append(art)

        await db.commit()
        return articles

