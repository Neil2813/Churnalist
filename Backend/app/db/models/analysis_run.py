"""AnalysisRun ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AnalysisStatus, PipelineStage
from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.event import Event


class AnalysisRun(Base, UUIDMixin):
    """
    An auditable record of a complete pipeline execution.

    Every time the 5-agent pipeline runs for an event, an AnalysisRun
    is created. This makes analysis reproducible and auditable.
    """
    __tablename__ = "analysis_runs"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )

    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")

    status: Mapped[str] = mapped_column(
        String(32),
        default=AnalysisStatus.QUEUED,
        nullable=False,
        index=True,
    )

    current_stage: Mapped[str] = mapped_column(
        String(64),
        default=PipelineStage.SOURCE_HUNTING,
        nullable=False,
    )

    # Progress percentage 0–100
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Counters
    articles_processed: Mapped[int] = mapped_column(Integer, default=0)
    claims_processed: Mapped[int] = mapped_column(Integer, default=0)
    relations_created: Mapped[int] = mapped_column(Integer, default=0)
    corrections_found: Mapped[int] = mapped_column(Integer, default=0)

    # Failure info
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Aggregate timing and token metrics stored as JSON
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    event: Mapped["Event"] = relationship("Event", back_populates="analysis_runs")

    def __repr__(self) -> str:
        return (
            f"<AnalysisRun id={self.id!r} event={self.event_id!r} "
            f"status={self.status!r} progress={self.progress}%>"
        )
