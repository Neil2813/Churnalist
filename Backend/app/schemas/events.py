"""Pydantic schemas for Event records and discovery operations."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import EventStatus, TimePrecision
from app.schemas.articles import ArticleResponse


class EventCreate(BaseModel):
    """Payload for creating a new Event manually or via discovery."""
    title: str
    canonical_summary: str | None = None
    topic: str | None = None
    location_name: str | None = None
    event_time: datetime | None = None
    time_precision: TimePrecision = TimePrecision.UNKNOWN


class EventResponse(BaseModel):
    """Summary representation of an Event."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    canonical_summary: str | None = None
    topic: str | None = None
    location_name: str | None = None
    event_time: datetime | None = None
    time_precision: TimePrecision | str = TimePrecision.UNKNOWN
    status: EventStatus | str = EventStatus.DISCOVERED
    canonical_hash: str | None = None
    article_count: int = 0
    created_at: datetime
    updated_at: datetime


class EventDetailResponse(EventResponse):
    """Detailed view of an Event including its clustered articles."""
    articles: list[ArticleResponse] = Field(default_factory=list)


class EventDiscoverRequest(BaseModel):
    """Request payload to initiate event discovery from a seed URL or topic."""
    url: str | None = None
    seed_url: str | None = None
    topic: str | None = None
    keywords: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    max_articles: int = Field(default=10, ge=1, le=50)


class EventDiscoverResponse(BaseModel):
    """Response payload returned when investigation is queued."""
    id: str
    event_id: str
    run_id: str
    status: str = "QUEUED"

