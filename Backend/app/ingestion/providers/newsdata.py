"""
NewsData.io free API provider.

Free tier: 200 requests/day, no credit card required.
API docs: https://newsdata.io/documentation

Supports Hindi, Tamil, Telugu, Bengali natively — useful for multilingual coverage.
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.constants import ProviderName
from app.core.exceptions import NewsProviderError, NewsProviderRateLimitError
from app.core.logging import get_logger
from app.ingestion.article_extractor import RawArticle, fetch_and_extract
from app.utils.dates import parse_date
from app.utils.hashing import content_hash
from app.utils.urls import normalize_url, url_to_hash

logger = get_logger(__name__)

NEWSDATA_BASE = "https://newsdata.io/api/1"

# NewsData language code mapping
LANGUAGE_MAP = {
    "en": "en", "hi": "hi", "ta": "ta",
    "te": "te", "bn": "bn", "mr": "mr",
    "gu": "gu", "ml": "ml", "kn": "kn",
}


class NewsDataProvider:
    """
    NewsData.io API provider.

    Falls back gracefully when NEWSDATA_API_KEY is not configured.
    Supports broad multilingual coverage across Indian languages.
    """

    provider_name = ProviderName.NEWSDATA

    def __init__(self) -> None:
        self.api_key = get_settings().newsdata_api_key

    async def search(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient,
    ) -> list[RawArticle]:
        if not self.api_key:
            logger.debug("newsdata_no_api_key", msg="NEWSDATA_API_KEY not set, skipping NewsData provider")
            return []

        # NewsData accepts comma-separated language codes
        lang_codes = ",".join(
            LANGUAGE_MAP[l] for l in (languages or ["en"]) if l in LANGUAGE_MAP
        ) or "en"

        params = {
            "apikey": self.api_key,
            "q": query,
            "language": lang_codes,
            "country": "in",
            "size": min(max_results, 10),
        }

        try:
            response = await http_client.get(f"{NEWSDATA_BASE}/news", params=params)

            if response.status_code == 429:
                raise NewsProviderRateLimitError("NewsData rate limit exceeded")
            if response.status_code != 200:
                raise NewsProviderError(f"NewsData API returned {response.status_code}")

            data = response.json()
        except Exception as e:
            logger.warning("newsdata_request_failed_or_rate_limited", error=str(e))
            return []

        articles = []
        for item in (data.get("results") or [])[:max_results]:
            article = await self._item_to_raw_article(item, languages, http_client)
            if article:
                articles.append(article)

        logger.info("newsdata_search_done", query=query, count=len(articles))
        return articles

    async def fetch_one(
        self,
        url: str,
        *,
        http_client: httpx.AsyncClient,
    ) -> RawArticle | None:
        try:
            return await fetch_and_extract(url, http_client)
        except Exception as e:
            logger.warning("newsdata_fetch_one_failed", url=url, error=str(e))
            return None

    async def _item_to_raw_article(
        self,
        item: dict,
        languages: list[str] | None,
        http_client: httpx.AsyncClient,
    ) -> RawArticle | None:
        from datetime import datetime, timezone

        url = item.get("link")
        if not url:
            return None

        item_lang = item.get("language") or (languages[0] if languages else "en")

        try:
            article = await fetch_and_extract(url, http_client)
        except Exception:
            # Fallback to API-provided content (often just a snippet)
            body = item.get("full_description") or item.get("description") or item.get("content") or ""
            article = RawArticle(
                url=url,
                canonical_url=normalize_url(url),
                url_hash=url_to_hash(normalize_url(url)),
                title=item.get("title"),
                content=body,
                content_hash=content_hash(body) if body else None,
                language=item_lang,
                published_at=parse_date(item.get("pubDate")),
                retrieved_at=datetime.now(timezone.utc),
                extraction_status="PARTIAL",
                source_name=item.get("source_id"),
            )

        if not article.title:
            article.title = item.get("title")
        if not article.published_at:
            article.published_at = parse_date(item.get("pubDate"))
        if not article.source_name:
            article.source_name = item.get("source_id")
        if not article.language:
            article.language = item_lang

        return article
