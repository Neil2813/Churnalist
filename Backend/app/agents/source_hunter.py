"""
Agent 1: Source Hunter.

Responsible for discovering relevant news articles for an event live across news providers,
normalizing metadata, generating event fingerprints, and deduplicating representations.
"""
from __future__ import annotations

import asyncio
import hashlib
import httpx
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
        Fetch news articles live from all configured APIs.
        Ignores providers silently if their rate limit or quota is exceeded.
        """
        from app.ingestion.providers.duckduckgo import DuckDuckGoProvider
        providers = [
            DuckDuckGoProvider(),
            GNewsProvider(),
            NewsDataProvider(),
            MediastackProvider(),
            CurrentsProvider(),
            TheNewsAPIProvider(),
            GuardianProvider(),
            SpaceflightProvider(),
            NewsFlashProvider(),
        ]


        raw_articles: list[RawArticle] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            tasks = [
                p.search(query, max_results=max_articles_per_provider, http_client=client)
                for p in providers
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    for article in res:
                        if article.url and article.url not in seen_urls:
                            seen_urls.add(article.url)
                            raw_articles.append(article)
                elif isinstance(res, Exception):
                    logger.warning("live_provider_fetch_exception", error=str(res))

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
        Live ingest and normalize articles from seed_url or live news API search.
        """
        articles: list[Article] = []
        derived_keywords: list[str] = list(keywords or [])

        # 1. Direct seed URL ingestion
        if seed_url and db:
            try:
                ingested = await self.orchestrator.ingest_single_url(db, seed_url, event_id=event_id)
                if ingested:
                    articles.append(ingested)

                    # Update event title if event_id is given and title is generic
                    if event_id:
                        from app.db.repositories.event_repository import EventRepository
                        event = await EventRepository.get_by_id(db, event_id)
                        if event and (event.title.startswith("Event from") or event.title.startswith("Discovered Event")):
                            if ingested.title and ingested.title != "Untitled Article":
                                event.title = ingested.title
                                await db.commit()

                    # Extract search keywords from scraped article if none provided
                    if not derived_keywords:
                        stop_words = {
                            "a", "an", "the", "and", "or", "but", "if", "because", "as", "until", "while",
                            "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
                            "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
                            "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
                            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
                            "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
                            "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
                            "should", "now", "says", "said", "new", "news", "event", "report", "reports"
                        }
                        entities = extract_named_entities(f"{ingested.title or ''} {ingested.content or ''}")
                        title_terms = [
                            w.strip('.,!"\'()[]{}') for w in (ingested.title or "").split()
                            if w.lower().strip('.,!"\'()[]{}') not in stop_words and len(w) > 2
                        ]
                        for item in entities + title_terms:
                            if item and item.lower() not in [k.lower() for k in derived_keywords]:
                                derived_keywords.append(item)
                                if len(derived_keywords) >= 6:
                                    break
            except Exception as e:
                logger.warning("seed_url_ingestion_failed", url=seed_url, error=str(e))

        # 2. Live API query ingestion for same exact news story
        query_terms = derived_keywords
        if query_terms and db:
            query_str = " ".join(query_terms[:5])
            raw_docs = await self.fetch_live_news(query_str, max_articles_per_provider=max_articles)
            for raw_doc in raw_docs:
                if len(articles) >= max_articles:
                    break
                try:
                    ingested = await self.orchestrator.ingest_single_url(db, raw_doc.url, event_id=event_id)
                    if ingested and ingested.id not in {a.id for a in articles}:
                        articles.append(ingested)
                except Exception as e:
                    logger.warning("live_article_ingestion_failed", url=raw_doc.url, error=str(e))

        return articles

