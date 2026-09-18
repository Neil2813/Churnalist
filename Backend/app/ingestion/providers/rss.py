"""RSS/Atom Feed Ingestion Provider."""
from __future__ import annotations

from typing import Any

import feedparser
import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.ingestion.base import BaseProvider, RawDocument
from app.ingestion.normalizer import ArticleNormalizer

logger = get_logger(__name__)
settings = get_settings()


class RSSProvider(BaseProvider):
    """
    Ingest articles from an RSS or Atom feed.
    """

    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        self.timeout = float(settings.request_timeout_seconds)

    @property
    def provider_name(self) -> str:
        return f"rss:{self.feed_url}"

    async def fetch_latest(self, limit: int = 20) -> list[RawDocument]:
        """Fetch and parse latest feed entries."""
        logger.info("fetching_rss_feed", feed_url=self.feed_url)

        headers = {
            "User-Agent": "DRIFT-Bot/1.0 RSSFetcher",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(self.feed_url, headers=headers)
                if response.status_code >= 400:
                    raise ExternalServiceError(f"Failed to fetch RSS feed {self.feed_url}: HTTP {response.status_code}")
                feed_content = response.text
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"HTTP error fetching RSS feed {self.feed_url}: {exc}") from exc

        parsed = feedparser.parse(feed_content)
        if parsed.bozo and not parsed.entries:
            logger.warning("rss_parse_warning", feed_url=self.feed_url, exception=str(getattr(parsed, "bozo_exception", "")))

        raw_documents: list[RawDocument] = []
        feed_title = parsed.feed.get("title", "")
        feed_lang = parsed.feed.get("language", None)

        for entry in parsed.entries[:limit]:
            url = entry.get("link") or entry.get("id")
            if not url:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary") or entry.get("description") or ""

            # Check for full content in feed
            content = None
            if "content" in entry and entry.content:
                content = entry.content[0].get("value")

            published_str = entry.get("published") or entry.get("updated")
            published_at = ArticleNormalizer.parse_published_date(published_str)

            author = entry.get("author")

            raw_documents.append(
                RawDocument(
                    url=url,
                    title=title.strip() if title else None,
                    content=content or summary,
                    raw_html=content or summary,
                    published_at=published_at,
                    author=author,
                    language=feed_lang,
                    source_name=feed_title,
                    metadata={"feed_url": self.feed_url, "feed_entry_id": entry.get("id")}
                )
            )

        logger.info("rss_feed_fetched", feed_url=self.feed_url, count=len(raw_documents))
        return raw_documents

    async def fetch_by_url(self, url: str) -> RawDocument | None:
        """Fetch a specific feed item by URL."""
        docs = await self.fetch_latest(limit=50)
        for doc in docs:
            if doc.url == url:
                return doc
        return None
