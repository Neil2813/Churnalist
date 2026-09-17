"""Pydantic schemas for ingestion operations and job tracking."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from app.core.constants import IngestionStatus, SourceType


class IngestUrlRequest(BaseModel):
    """Payload to ingest a single web article by URL."""
    url: HttpUrl = Field(..., description="The direct article URL to fetch and parse.")
    event_id: str | None = Field(default=None, description="Optional Event ID to associate the article with.")
    source_type: SourceType = Field(default=SourceType.NEWSROOM, description="Origin source type of the article.")


class IngestRssRequest(BaseModel):
    """Payload to trigger RSS/Atom feed ingestion."""
    rss_url: HttpUrl = Field(..., description="The RSS/Atom feed URL to fetch and parse.")
    event_id: str | None = Field(default=None, description="Optional Event ID to associate articles with.")
    max_items: int = Field(default=20, ge=1, le=100, description="Maximum number of feed items to ingest.")


class IngestionJobResponse(BaseModel):
    """Ingestion job execution and status response."""
    id: str
    provider: str
    query: str | None = None
    event_id: str | None = None
    status: IngestionStatus
    started_at: datetime
    completed_at: datetime | None = None
    documents_found: int = 0
    documents_added: int = 0
    documents_skipped: int = 0
    documents_failed: int = 0
    error_message: str | None = None
    metadata_json: str | None = None

    class Config:
        from_attributes = True
