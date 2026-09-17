"""Pydantic schemas for news sources and outlets."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.core.constants import SourceType


class SourceCreate(BaseModel):
    """Payload to register a new news outlet or feed source."""
    name: str = Field(..., description="Name of the news outlet or wire service.")
    domain: str = Field(..., description="Root domain (e.g. reuters.com).")
    base_url: HttpUrl = Field(..., description="Base homepage URL.")
    source_type: SourceType = Field(default=SourceType.NEWSROOM)
    language: str | None = Field(default=None, description="Primary language code (e.g. en, hi, ta).")
    feed_url: HttpUrl | None = Field(default=None, description="Optional RSS/Atom feed URL.")


class SourceResponse(BaseModel):
    """Registered news source response model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    domain: str
    base_url: str
    source_type: SourceType
    language: str | None = None
    feed_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
