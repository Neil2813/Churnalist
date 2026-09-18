"""Manual URL submission ingestion provider."""
from __future__ import annotations

from app.ingestion.base import BaseProvider, RawDocument


class ManualProvider(BaseProvider):
    """
    Provider for manually submitted article URLs or raw HTML documents.
    """

    def __init__(self, target_url: str | None = None):
        self.target_url = target_url

    @property
    def provider_name(self) -> str:
        return "manual"

    async def fetch_latest(self, limit: int = 20) -> list[RawDocument]:
        if self.target_url:
            doc = await self.fetch_by_url(self.target_url)
            return [doc] if doc else []
        return []

    async def fetch_by_url(self, url: str) -> RawDocument | None:
        return RawDocument(
            url=url,
            source_name="Manual Entry",
            metadata={"submission_type": "manual_url"}
        )
