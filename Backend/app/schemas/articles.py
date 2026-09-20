"""Pydantic schemas for Article records and version history."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ExtractionStatus, SourceType


class ArticleVersionResponse(BaseModel):
    """Snapshot version of an article's previous content."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    article_id: str
    version_number: int
    content_hash: str
    retrieved_at: datetime
    change_type: str | None = None
    change_summary: str | None = None


class ArticleResponse(BaseModel):
    """Summary representation of an ingested news article."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str | None = None
    source_id: str | None = None

    url: str
    canonical_url: str | None = None
    url_hash: str

    title: str | None = None
    subtitle: str | None = None
    author: str | None = None

    language: str | None = None
    language_confidence: float | None = None
    country: str | None = None

    published_at: datetime | None = None
    retrieved_at: datetime | None = None

    source_type: SourceType | str = SourceType.OTHER
    extraction_status: ExtractionStatus | str = ExtractionStatus.FULL

    created_at: datetime
    updated_at: datetime


class ArticleDetailResponse(ArticleResponse):
    """Detailed view of an article including full text and version history."""
    content: str | None = None
    content_hash: str | None = None
    metadata_json: str | None = None
    versions: list[ArticleVersionResponse] = Field(default_factory=list)


class ArticleTranslationResponse(BaseModel):
    """Full-article translation response with caching metadata and original text for toggle."""
    model_config = ConfigDict(from_attributes=True)

    article_id: str
    target_language: str
    target_language_name: str
    translated_title: str | None = None
    translated_content: str
    original_language: str | None = None
    original_language_name: str | None = None
    original_title: str | None = None
    original_content: str | None = None
    cached: bool = False
    created_at: datetime
