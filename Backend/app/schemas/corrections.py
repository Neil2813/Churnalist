"""Pydantic schemas for Correction tracking records."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import CorrectionType


class CorrectionResponse(BaseModel):
    """Schema representing an identified correction or retraction."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    article_id: str
    original_claim_id: str | None = None
    corrected_claim_id: str | None = None

    correction_type: CorrectionType
    original_text: str
    corrected_text: str
    correction_url: str | None = None

    outdated_articles_count: int = 0
    outdated_article_ids: list[str] = Field(default_factory=list)

    detected_at: datetime
    created_at: datetime
