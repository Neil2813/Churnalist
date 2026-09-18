"""Spaceflight News API provider (v4)."""
from __future__ import annotations

import httpx
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.constants import ProviderName
from app.core.logging import get_logger
from app.ingestion.base import BaseProvider, RawDocument
from app.ingestion.article_extractor import RawArticle
from app.utils.dates import parse_date
from app.utils.hashing import content_hash
from app.utils.urls import normalize_url, url_to_hash

logger = get_logger(__name__)


class SpaceflightProvider(BaseProvider):
    """
    Spaceflight News API (v4) provider.
    Public API endpoint (no authentication key required).
    Handles rate limits and API errors gracefully without raising exceptions.
    """

    provider_name = ProviderName.SPACEFLIGHT

    def __init__(self, query: str = "space") -> None:
        self.query = query
        self.base_url = get_settings().spaceflight_url.rstrip("/")

    async def fetch_latest(self, limit: int = 20) -> list[RawDocument]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                articles = await self.search(self.query, max_results=limit, http_client=client)
                return [
                    RawDocument(
                        url=a.url,
                        title=a.title,
                        content=a.content,
                        published_at=a.published_at,
                        language="en",
                        source_name=a.source_name or "Spaceflight News",
                        metadata={"search_query": self.query},
                    )
                    for a in articles
                ]
        except Exception as e:
            logger.warning("spaceflight_fetch_latest_failed", error=str(e))
            return []

    async def fetch_by_url(self, url: str) -> RawDocument | None:
        return None

    async def search(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient,
    ) -> list[RawArticle]:
        params = {
            "search": query,
            "limit": min(max_results, 20),
        }

        try:
            response = await http_client.get(f"{self.base_url}/", params=params)

            if response.status_code in (429, 403, 401, 402):
                logger.warning("spaceflight_rate_limit_exceeded", status_code=response.status_code)
                return []
            if response.status_code != 200:
                logger.warning("spaceflight_api_non_200", status_code=response.status_code)
                return []

            data = response.json()
            items = data.get("results") or []
            articles: list[RawArticle] = []

            for item in items[:max_results]:
                url = item.get("url")
                if not url:
                    continue
                body = item.get("summary") or item.get("title") or ""
                art = RawArticle(
                    url=url,
                    canonical_url=normalize_url(url),
                    url_hash=url_to_hash(normalize_url(url)),
                    title=item.get("title"),
                    content=body,
                    content_hash=content_hash(body) if body else None,
                    language="en",
                    published_at=parse_date(item.get("published_at")),
                    retrieved_at=datetime.now(timezone.utc),
                    extraction_status="PARTIAL",
                    source_name=item.get("news_site") or "Spaceflight News",
                )
                articles.append(art)

            logger.info("spaceflight_search_done", query=query, count=len(articles))
            return articles
        except Exception as exc:
            logger.warning("spaceflight_request_failed", query=query, error=str(exc))
            return []
