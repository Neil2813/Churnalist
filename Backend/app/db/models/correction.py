"""Correction ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import CorrectionType
from app.db.base import Base, UUIDMixin


class Correction(Base, UUIDMixin):
    """
    A detected correction, update, clarification, or retraction.

    A correction links to the event, optionally to a specific article,
    and references the original + corrected claim text with full evidence.
    """
    __tablename__ = "corrections"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    article_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    correction_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction_text: Mapped[str] = mapped_column(Text, nullable=False)

    correction_type: Mapped[str] = mapped_column(
        String(64),
        default=CorrectionType.OTHER,
        nullable=False,
    )

    # Plain-text representations of the change
    original_claim_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_claim_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional FK links to structured claims
    original_claim_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True
    )
    corrected_claim_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True
    )

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # JSON: {"surviving_article_ids": [...], "updated_article_ids": [...]}
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Correction id={self.id!r} type={self.correction_type!r} "
            f"event={self.event_id!r}>"
        )
