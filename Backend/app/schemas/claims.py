"""Pydantic schemas for Claim records and Claim Relations."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ClaimType, RelationType, ConfidenceLevel


class ClaimCreate(BaseModel):
    """Payload for creating a Claim."""
    article_id: str
    event_id: str
    claim_type: ClaimType
    subject: str
    predicate: str
    object_value: str
    object_unit: str | None = None
    location: str | None = None
    event_time: datetime | str | None = None
    attribution: str | None = None
    certainty: str | None = None
    modality: str | None = None
    severity: str | None = None
    raw_text: str
    source_start_offset: int | None = None
    source_end_offset: int | None = None
    normalized_value_json: dict[str, Any] | None = None


class ClaimResponse(BaseModel):
    """Representation of an extracted Claim."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    article_id: str

    claim_type: ClaimType
    subject: str
    predicate: str
    object_value: str
    object_unit: str | None = None

    location: str | None = None
    event_time: str | None = None

    attribution: str | None = None
    certainty: str | None = None
    modality: str | None = None
    severity: str | None = None

    raw_text: str
    source_start_offset: int | None = None
    source_end_offset: int | None = None

    created_at: datetime
    updated_at: datetime


class ClaimRelationResponse(BaseModel):
    """Representation of a connection between two claims across articles/languages."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


    id: str
    source_claim_id: str
    target_claim_id: str
    relation_type: RelationType
    confidence: float | ConfidenceLevel = 1.0
    reason: str | None = None
    evidence_json: dict[str, Any] | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    created_at: datetime
