"""ClaimRelation ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RelationType
from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.claim import Claim


class ClaimRelation(Base, UUIDMixin):
    """
    A directed relationship between two claims.

    This is the core product artefact of DRIFT:
    it records *how* a claim changed between two articles,
    with full audit trail including model name, prompt version,
    and confidence.

    Every visible drift in the UI must have a corresponding ClaimRelation.
    """
    __tablename__ = "claim_relations"

    # The originating claim (may be None for ADDED claims)
    source_claim_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # The target claim being compared to the source
    target_claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )

    relation_type: Mapped[str] = mapped_column(
        String(64),
        default=RelationType.SAME,
        nullable=False,
        index=True,
    )

    # Score in [0, 1]
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Human-readable explanation of the relation
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured evidence: source span, target span, model output, etc.
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit: which model and prompt produced this relation
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    source_claim: Mapped["Claim | None"] = relationship(
        "Claim",
        foreign_keys=[source_claim_id],
        back_populates="source_relations",
    )
    target_claim: Mapped["Claim"] = relationship(
        "Claim",
        foreign_keys=[target_claim_id],
        back_populates="target_relations",
    )

    def __repr__(self) -> str:
        return (
            f"<ClaimRelation {self.source_claim_id!r} → {self.relation_type!r} "
            f"→ {self.target_claim_id!r} conf={self.confidence:.2f}>"
        )
