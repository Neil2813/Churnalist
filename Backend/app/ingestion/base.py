"""Base classes and data containers for ingestion providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.constants import SourceType


@dataclass
class RawDocument:
    """
    Standardized payload emitted by ingestion providers before HTML parsing and normalization.
    """
    url: str
    title: str | None = None
    content: str | None = None
    raw_html: str | None = None
    published_at: datetime | None = None
    author: str | None = None
    language: str | None = None
    source_type: SourceType = SourceType.NEWSROOM
    source_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract interface that all DRIFT news providers must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for the ingestion provider."""
        ...

    @abstractmethod
    async def fetch_latest(self, limit: int = 20) -> list[RawDocument]:
        """Fetch latest available articles/feed items from the provider."""
        ...

    @abstractmethod
    async def fetch_by_url(self, url: str) -> RawDocument | None:
        """Fetch a specific document by its direct URL."""
        ...
