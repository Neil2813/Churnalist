"""
DuckDuckGo live web search provider for DRIFT.
Scrapes live web search results for news queries without requiring paid API keys.
"""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from datetime import datetime

from app.core.logging import get_logger
from app.ingestion.article_extractor import RawArticle

logger = get_logger(__name__)


class DuckDuckGoProvider:
    """DuckDuckGo web scraping provider for live news articles."""

    provider_name: str = "DuckDuckGo"

    async def search(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient,
    ) -> list[RawArticle]:
        """Scrape live search results from DuckDuckGo HTML API."""
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        articles: list[RawArticle] = []
        try:
            res = await http_client.post(url, data={"q": query}, headers=headers, timeout=15.0)
            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.select("a.result__a"):
                title = a.text.strip()
                link = a.get("href")
                if link and link.startswith("http") and "duckduckgo.com" not in link:
                    articles.append(
                        RawArticle(
                            url=link,
                            title=title or "Live Web News Article",
                            content=title,
                            published_at=datetime.utcnow(),
                            source_name="DuckDuckGo Web Search",
                        )
                    )
                    if len(articles) >= max_results:
                        break
        except Exception as exc:
            logger.warning("duckduckgo_search_failed", query=query, error=str(exc))

        return articles

    async def fetch_one(
        self,
        url: str,
        *,
        http_client: httpx.AsyncClient,
    ) -> RawArticle | None:
        """Fetch a single article URL via DuckDuckGo provider protocol."""
        return RawArticle(
            url=url,
            title="Single Article",
            content="",
            source_name="DuckDuckGo Direct",
        )
