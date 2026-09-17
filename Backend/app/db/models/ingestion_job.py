"""IngestionJob ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import IngestionStatus, ProviderName
from app.db.base import Base, UUIDMixin


class IngestionJob(Base, UUIDMixin):
    """
    Records every ingestion operation so ingestion is observable.

    Each call to a news provider (RSS, GNews, NewsData, manual URL)
    creates an IngestionJob so we can track success/failure rates,
    quota consumption, and duplicate rates per provider.
    """
    __tablename__ = "ingestion_jobs"

    provider: Mapped[str] = mapped_column(
        String(64),
        default=ProviderName.MANUAL,
        nullable=False,
        index=True,
    )
    query: Mapped[str | None] = mapped_column(Text, nullable=True)

    event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default=IngestionStatus.QUEUED,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Counters
    documents_found: Mapped[int] = mapped_column(Integer, default=0)
    documents_added: Mapped[int] = mapped_column(Integer, default=0)
    documents_skipped: Mapped[int] = mapped_column(Integer, default=0)
    documents_failed: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON: provider-specific metadata, rate-limit info, etc.
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<IngestionJob id={self.id!r} provider={self.provider!r} "
            f"status={self.status!r} found={self.documents_found}>"
        )
