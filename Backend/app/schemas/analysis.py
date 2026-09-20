"""Pydantic schemas for Analysis operations, Churnalism, and Drift results."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import AnalysisStatus, PipelineStage


class AnalysisRunRequest(BaseModel):
    """Payload to trigger an event analysis run."""
    event_id: str
    include_churnalism: bool = True
    include_multilingual_drift: bool = True
    include_corrections: bool = True


class SourceOverlapResponse(BaseModel):
    """Result metrics for churnalism / source overlap analysis."""
    source_article_id: str
    target_article_id: str
    source_overlap: float
    sentence_overlap: float
    entity_overlap: float
    numeric_overlap: float
    copied_claims_count: int
    new_claims_count: int
    substantive_new_information: list[str] = Field(default_factory=list)
    assessment: str


class DriftMetricResponse(BaseModel):
    """Metric summarizing drift for an event across editions."""
    total_articles: int
    total_claims: int
    drifting_claims_count: int
    numerical_drifts_count: int
    attribution_losses_count: int
    severity_changes_count: int
    categories_breakdown: dict[str, int] = Field(default_factory=dict)


class AnalysisRunResponse(BaseModel):
    """Status and metrics of an analysis pipeline run."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    status: AnalysisStatus | str = AnalysisStatus.QUEUED
    current_stage: PipelineStage | str = PipelineStage.SOURCE_HUNTING
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    metrics_json: dict[str, Any] | None = None
