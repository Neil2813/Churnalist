"""
News provider protocol and shared RawArticle definition.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx

from app.ingestion.article_extractor import RawArticle


@runtime_checkable
class NewsProvider(Protocol):
    """
    All ingestion providers implement this interface.

    The application does not need to know which provider produced
    an article; all providers return the same RawArticle type.
    """

    provider_name: str

    async def search(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient,
    ) -> list[RawArticle]:
        """
        Search for articles matching the query.

        Must handle provider errors internally and return an empty list
        on failure (never propagate provider-specific exceptions to callers).
        """
        ...

    async def fetch_one(
        self,
        url: str,
        *,
        http_client: httpx.AsyncClient,
    ) -> RawArticle | None:
        """Fetch and extract a single article by URL."""
        ...
