"""Google News provider supporting both GNews REST API and RSS fallback."""
from __future__ import annotations

import httpx
from urllib.parse import quote_plus
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.constants import ProviderName
from app.core.logging import get_logger
from app.ingestion.base import BaseProvider, RawDocument
from app.ingestion.article_extractor import RawArticle, fetch_and_extract
from app.ingestion.providers.rss import RSSProvider
from app.utils.dates import parse_date
from app.utils.hashing import content_hash
from app.utils.urls import normalize_url, url_to_hash

logger = get_logger(__name__)

GNEWS_API_BASE = "https://gnews.io/api/v4"


class GNewsProvider(BaseProvider):
    """
    Google News API & RSS provider.

    Uses GNews REST API if GNEWS_API_KEY is configured.
    Falls back to Google News RSS feed if API key is not present or rate limited.
    Never surfaces rate limits or quota errors to callers.
    """

    def __init__(self, query: str = "news", hl: str = "en-US", gl: str = "US") -> None:
        self.query = query
        self.hl = hl
        self.gl = gl
        self.api_key = get_settings().gnews_api_key
        encoded_q = quote_plus(query)
        self.rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={gl}&ceid={gl}:{hl.split('-')[0]}"
        self._delegate = RSSProvider(self.rss_url)

    @property
    def provider_name(self) -> str:
        return f"gnews:{self.query}"

    async def fetch_latest(self, limit: int = 20) -> list[RawDocument]:
        """Fetch latest documents via GNews API or RSS fallback."""
        if self.api_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    articles = await self.search_api(self.query, max_results=limit, http_client=client)
                    if articles:
                        docs: list[RawDocument] = []
                        for a in articles:
                            docs.append(
                                RawDocument(
                                    url=a.url,
                                    title=a.title,
                                    content=a.content,
                                    published_at=a.published_at,
                                    language=a.language or "en",
                                    source_name=a.source_name or "Google News",
                                    metadata={"search_query": self.query},
                                )
                            )
                        return docs
            except Exception as e:
                logger.warning("gnews_rest_api_fetch_failed_using_rss_fallback", error=str(e))

        docs = await self._delegate.fetch_latest(limit=limit)
        for doc in docs:
            doc.metadata["search_query"] = self.query
            doc.source_name = "Google News Search"
        return docs

    async def fetch_by_url(self, url: str) -> RawDocument | None:
        return await self._delegate.fetch_by_url(url)

    async def search(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient,
    ) -> list[RawArticle]:
        """Search GNews REST API or RSS feed silently on error."""
        if self.api_key:
            results = await self.search_api(query, languages=languages, max_results=max_results, http_client=http_client)
            if results:
                return results

        # Fallback to RSS search
        try:
            encoded_q = quote_plus(query)
            rss_provider = RSSProvider(f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en")
            raw_docs = await rss_provider.fetch_latest(limit=max_results)
            articles: list[RawArticle] = []
            for doc in raw_docs:
                try:
                    art = await fetch_and_extract(doc.url, http_client)
                except Exception:
                    body = doc.content or ""
                    art = RawArticle(
                        url=doc.url,
                        canonical_url=normalize_url(doc.url),
                        url_hash=url_to_hash(normalize_url(doc.url)),
                        title=doc.title,
                        content=body,
                        content_hash=content_hash(body) if body else None,
                        language=doc.language or "en",
                        published_at=doc.published_at,
                        retrieved_at=datetime.now(timezone.utc),
                        extraction_status="PARTIAL",
                        source_name="Google News RSS",
                    )
                articles.append(art)
            return articles
        except Exception as exc:
            logger.warning("gnews_rss_search_failed", query=query, error=str(exc))
            return []

    async def search_api(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient,
    ) -> list[RawArticle]:
        if not self.api_key:
            return []

        lang = languages[0] if languages else "en"
        params = {
            "q": query,
            "apikey": self.api_key,
            "lang": lang,
            "max": min(max_results, 10),
        }

        try:
            response = await http_client.get(f"{GNEWS_API_BASE}/search", params=params)
            if response.status_code in (429, 403, 401, 402):
                logger.warning("gnews_rate_limit_or_quota_exceeded", status_code=response.status_code)
                return []
            if response.status_code != 200:
                logger.warning("gnews_api_non_200", status_code=response.status_code)
                return []

            data = response.json()
            items = data.get("articles") or []
            articles: list[RawArticle] = []

            for item in items[:max_results]:
                url = item.get("url")
                if not url:
                    continue
                body = item.get("content") or item.get("description") or ""
                art = RawArticle(
                    url=url,
                    canonical_url=normalize_url(url),
                    url_hash=url_to_hash(normalize_url(url)),
                    title=item.get("title"),
                    content=body,
                    content_hash=content_hash(body) if body else None,
                    language=lang,
                    published_at=parse_date(item.get("publishedAt")),
                    retrieved_at=datetime.now(timezone.utc),
                    extraction_status="PARTIAL",
                    source_name=(item.get("source") or {}).get("name") or "GNews",
                )
                articles.append(art)

            logger.info("gnews_search_done", query=query, count=len(articles))
            return articles
        except Exception as exc:
            logger.warning("gnews_api_request_failed", query=query, error=str(exc))
            return []
