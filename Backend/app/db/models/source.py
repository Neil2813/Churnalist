"""Source ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SourceType
from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.article import Article


class Source(Base, UUIDMixin, TimestampMixin):
    """
    Represents a news publisher or information source.

    Tracks the domain, source type, language, and optional RSS feed URL
    for each publisher so provenance can be attributed correctly.
    """
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_type: Mapped[str] = mapped_column(
        String(32),
        default=SourceType.OTHER,
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    articles: Mapped[list["Article"]] = relationship(
        "Article", back_populates="source", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id!r} name={self.name!r} domain={self.domain!r}>"
