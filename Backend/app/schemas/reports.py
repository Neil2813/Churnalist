"""Pydantic schemas for Agent 5 Truth Trail generated reports."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DriftHighlight(BaseModel):
    """Specific drift item highlighted in report."""
    category: str
    source_language: str
    target_language: str
    original_text: str
    drifted_text: str
    explanation: str
    severity_level: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH"


class CorrectionHighlight(BaseModel):
    """Correction status highlighted in report."""
    original_claim: str
    corrected_claim: str
    updated_articles_count: int
    outdated_articles_count: int
    details: str


class ReportResponse(BaseModel):
    """Human-readable, evidence-first provenance report."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    headline: str
    summary: str
    accuracy_analysis: str | None = None
    first_publisher: str | None = None
    first_published_at: str | None = None
    churn_analysis: str | None = None
    key_drifts: list[DriftHighlight] = Field(default_factory=list)
    correction_status: CorrectionHighlight | None = None
    reader_takeaway: str
    confidence_score: float = 0.9
    evidence_sources: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

