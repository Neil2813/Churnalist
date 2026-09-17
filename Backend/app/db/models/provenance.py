"""ProvenanceEdge ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ProvenanceRelation
from app.db.base import Base, UUIDMixin


class ProvenanceEdge(Base, UUIDMixin):
    """
    A directed edge in the provenance graph.

    Intentionally generic — from_entity_type / to_entity_type can be
    'article', 'claim', 'source', 'correction', etc. so the frontend
    can build a React Flow graph without knowing backend internals.

    Example:
        GovernmentRelease ─SOURCE_OF→ EnglishArticle
        EnglishArticle    ─TRANSLATED_TO→ TamilArticle
        TamilArticle      ─CORRECTED_BY→ Correction
    """
    __tablename__ = "provenance_edges"

    from_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    to_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    to_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    relation_type: Mapped[str] = mapped_column(
        String(64),
        default=ProvenanceRelation.SOURCE_OF,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # JSON: model output, overlap score, retrieval score, etc.
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ProvenanceEdge {self.from_entity_type}:{self.from_entity_id!r} "
            f"─{self.relation_type!r}→ "
            f"{self.to_entity_type}:{self.to_entity_id!r}>"
        )
