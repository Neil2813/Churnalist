"""Claim ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ClaimType
from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.article import Article
    from app.db.models.claim_relation import ClaimRelation
    from app.db.models.event import Event


class Claim(Base, UUIDMixin, TimestampMixin):
    """
    An atomic, structured claim extracted from an article.

    The claim is the fundamental unit of comparison in DRIFT.
    Two articles may use completely different wording but make the
    same claim; this table makes that computationally visible.

    Source spans (source_start_offset / source_end_offset) allow
    the UI to highlight exactly which sentence produced a claim.
    """
    __tablename__ = "claims"

    # Parent references
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Claim classification
    claim_type: Mapped[str] = mapped_column(
        String(32),
        default=ClaimType.FACT,
        nullable=False,
        index=True,
    )

    # Semantic fields
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    predicate: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Context fields
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Epistemic metadata
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    certainty: Mapped[str | None] = mapped_column(String(128), nullable=True)
    modality: Mapped[str | None] = mapped_column(String(128), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Source provenance
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Normalized value for numeric drift detection
    # Stored as JSON: {"normalized_value": 17, "qualifier": null}
    normalized_value_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Embedding stored as JSON array (list[float])
    # For hackathon, we store embeddings inline in SQLite.
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="claims")
    event: Mapped["Event | None"] = relationship("Event")
    source_relations: Mapped[list["ClaimRelation"]] = relationship(
        "ClaimRelation",
        foreign_keys="ClaimRelation.source_claim_id",
        back_populates="source_claim",
        lazy="select",
    )
    target_relations: Mapped[list["ClaimRelation"]] = relationship(
        "ClaimRelation",
        foreign_keys="ClaimRelation.target_claim_id",
        back_populates="target_claim",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Claim id={self.id!r} type={self.claim_type!r} "
            f"subj={self.subject!r} pred={self.predicate!r} obj={self.object_value!r}>"
        )
