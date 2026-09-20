"""
SerpAPI discovery service for Churnalist backend.

Provides a search abstraction using SerpAPI with DuckDuckGo (or configured engine)
and graceful fallbacks.
"""
from __future__ import annotations

from typing import Any
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SerpAPIService:
    """
    Dedicated search service using SerpAPI with DuckDuckGo / configured engine.
    Interface: search(query, start_date=None, end_date=None, language=None, region=None)
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str | None = None,
        engine: str | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.serpapi_api_key
        self.provider = provider or settings.search_provider
        self.engine = engine or settings.search_engine

    async def search(
        self,
        query: str,
        start_date: str | None = None,
        end_date: str | None = None,
        language: str | None = None,
        region: str | None = None,
        limit: int = 15,
    ) -> list[dict[str, Any]]:
        """
        Execute search query and return normalized search results.

        Return format:
        [
            {
                "title": "...",
                "url": "...",
                "snippet": "...",
                "source": "...",
                "published_at": "...",
                "position": 1,
                "search_query": "...",
                "engine": "duckduckgo"
            }
        ]
        """
        results: list[dict[str, Any]] = []

        if self.api_key:
            try:
                results = await self._search_serpapi(
                    query=query,
                    start_date=start_date,
                    end_date=end_date,
                    language=language,
                    region=region,
                    limit=limit,
                )
            except Exception as exc:
                logger.warning("serpapi_search_error", query=query, error=str(exc))

        if not results:
            # Fallback to direct DuckDuckGo or query-matched fallback
            results = await self._search_fallback(query=query, limit=limit)

        return results

    async def _search_serpapi(
        self,
        query: str,
        start_date: str | None,
        end_date: str | None,
        language: str | None,
        region: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Perform search request to SerpAPI endpoint."""
        url = "https://serpapi.com/search.json"
        params: dict[str, Any] = {
            "q": query,
            "engine": self.engine,
            "api_key": self.api_key,
        }
        if language:
            params["kl"] = f"{language}-{language}"
        if start_date and end_date:
            # DuckDuckGo time constraint param if supported or query date append
            params["df"] = f"{start_date}..{end_date}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results: list[dict[str, Any]] = []
        organic_results = data.get("organic_results", [])
        for idx, item in enumerate(organic_results[:limit], start=1):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link") or item.get("url") or "",
                "snippet": item.get("snippet", ""),
                "source": item.get("source") or item.get("domain") or "Web Search",
                "published_at": item.get("date") or None,
                "position": idx,
                "search_query": query,
                "engine": self.engine,
                "raw_json": str(item),
            })
        return results

    async def _search_fallback(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Direct DuckDuckGo html scraper fallback if SerpAPI is not configured or fails."""
        results: list[dict[str, Any]] = []
        try:
            from bs4 import BeautifulSoup
            url = "https://html.duckduckgo.com/html/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, data={"q": query}, headers=headers)
                soup = BeautifulSoup(res.text, "html.parser")
                pos = 1
                for a in soup.select("a.result__a"):
                    title = a.text.strip()
                    link = a.get("href")
                    snippet_elem = a.find_parent("div", class_="result__body")
                    snippet = snippet_elem.text.strip() if snippet_elem else title
                    if link and link.startswith("http") and "duckduckgo.com" not in link:
                        results.append({
                            "title": title or "Web Search Result",
                            "url": link,
                            "snippet": snippet,
                            "source": "DuckDuckGo Direct",
                            "published_at": None,
                            "position": pos,
                            "search_query": query,
                            "engine": "duckduckgo",
                        })
                        pos += 1
                        if len(results) >= limit:
                            break
        except Exception as exc:
            logger.warning("fallback_duckduckgo_failed", query=query, error=str(exc))

        return results
