"""Event ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EventStatus, TimePrecision
from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.article import Article
    from app.db.models.analysis_run import AnalysisRun


class Event(Base, UUIDMixin, TimestampMixin):
    """
    Canonical representation of a real-world event.

    An event is the central organising unit. All articles, claims,
    corrections, and provenance edges attach to an event.
    """
    __tablename__ = "events"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(256), nullable=True)

    location_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_precision: Mapped[str] = mapped_column(
        String(32),
        default=TimePrecision.UNKNOWN,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default=EventStatus.DISCOVERED,
        nullable=False,
    )

    # Deterministic fingerprint for deduplication
    canonical_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    # Relationships
    articles: Mapped[list["Article"]] = relationship(
        "Article", back_populates="event", lazy="select"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="event", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id!r} title={self.title!r} status={self.status!r}>"
