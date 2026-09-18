"""TheNewsAPI news provider."""
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

THENEWSAPI_BASE = "https://api.thenewsapi.com/v1"


class TheNewsAPIProvider(BaseProvider):
    """
    TheNewsAPI news provider.
    Handles rate limits, payment limits, and quota errors gracefully without raising exceptions.
    """

    provider_name = ProviderName.THENEWSAPI

    def __init__(self, query: str = "news") -> None:
        self.query = query
        self.api_key = get_settings().thenewsapi_api_key

    async def fetch_latest(self, limit: int = 20) -> list[RawDocument]:
        if not self.api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                articles = await self.search(self.query, max_results=limit, http_client=client)
                return [
                    RawDocument(
                        url=a.url,
                        title=a.title,
                        content=a.content,
                        published_at=a.published_at,
                        language=a.language or "en",
                        source_name=a.source_name or "TheNewsAPI",
                        metadata={"search_query": self.query},
                    )
                    for a in articles
                ]
        except Exception as e:
            logger.warning("thenewsapi_fetch_latest_failed", error=str(e))
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
        if not self.api_key:
            logger.debug("thenewsapi_no_api_key", msg="THENEWSAPI_API_KEY not set")
            return []

        lang = languages[0] if languages else "en"
        params = {
            "api_token": self.api_key,
            "search": query,
            "language": lang,
            "limit": min(max_results, 10),
        }

        try:
            response = await http_client.get(f"{THENEWSAPI_BASE}/news/all", params=params)

            if response.status_code in (429, 403, 401, 402):
                logger.warning("thenewsapi_rate_limit_or_quota_exceeded", status_code=response.status_code)
                return []
            if response.status_code != 200:
                logger.warning("thenewsapi_api_non_200", status_code=response.status_code)
                return []

            data = response.json()
            items = data.get("data") or []
            articles: list[RawArticle] = []

            for item in items[:max_results]:
                url = item.get("url")
                if not url:
                    continue
                body = item.get("description") or item.get("snippet") or item.get("title") or ""
                art = RawArticle(
                    url=url,
                    canonical_url=normalize_url(url),
                    url_hash=url_to_hash(normalize_url(url)),
                    title=item.get("title"),
                    content=body,
                    content_hash=content_hash(body) if body else None,
                    language=lang,
                    published_at=parse_date(item.get("published_at")),
                    retrieved_at=datetime.now(timezone.utc),
                    extraction_status="PARTIAL",
                    source_name=item.get("source") or "TheNewsAPI",
                )
                articles.append(art)

            logger.info("thenewsapi_search_done", query=query, count=len(articles))
            return articles
        except Exception as exc:
            logger.warning("thenewsapi_request_failed", query=query, error=str(exc))
            return []
