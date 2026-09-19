"""Article and ArticleVersion ORM models."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ExtractionStatus, SourceType
from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.claim import Claim
    from app.db.models.event import Event
    from app.db.models.source import Source


class Article(Base, UUIDMixin, TimestampMixin):
    """
    A single news article or document ingested into the system.

    The content_hash is used for deduplication; the same article may
    appear at multiple URLs (syndication). Both url_hash and content_hash
    enforce uniqueness at the DB level.
    """
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_articles_url_hash"),
    )

    # Foreign keys
    event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # URLs
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Content
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtitle: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Language & geo
    language: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    language_confidence: Mapped[float | None] = mapped_column(nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Classification
    source_type: Mapped[str] = mapped_column(
        String(32),
        default=SourceType.OTHER,
        nullable=False,
    )
    extraction_status: Mapped[str] = mapped_column(
        String(16),
        default=ExtractionStatus.FULL,
        nullable=False,
    )

    # Structured metadata from extraction
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    event: Mapped["Event | None"] = relationship("Event", back_populates="articles")
    source: Mapped["Source | None"] = relationship("Source", back_populates="articles")
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="article", lazy="select"
    )
    versions: Mapped[list["ArticleVersion"]] = relationship(
        "ArticleVersion", back_populates="article", lazy="select"
    )
    translations: Mapped[list["ArticleTranslation"]] = relationship(
        "ArticleTranslation", back_populates="article", lazy="select", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id!r} lang={self.language!r} title={self.title!r:.40}>"


class ArticleVersion(Base, UUIDMixin):
    """
    Historical snapshots of an article's content.

    When a URL is re-fetched and the content has changed, the old version
    is preserved here. This is critical for correction detection.
    """
    __tablename__ = "article_versions"

    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    change_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    article: Mapped["Article"] = relationship("Article", back_populates="versions")

    def __repr__(self) -> str:
        return (
            f"<ArticleVersion article_id={self.article_id!r} "
            f"v={self.version_number} hash={self.content_hash[:8]!r}>"
        )


class ArticleTranslation(Base, UUIDMixin, TimestampMixin):
    """
    Cached full-article translation.

    Keyed by article_id + target_language to avoid re-translating
    the same article and language pair on repeated read requests.
    """
    __tablename__ = "article_translations"
    __table_args__ = (
        UniqueConstraint("article_id", "target_language", name="uq_article_translations_article_lang"),
    )

    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_language: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    translated_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    translated_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    article: Mapped["Article"] = relationship("Article", back_populates="translations")

    def __repr__(self) -> str:
        return (
            f"<ArticleTranslation article_id={self.article_id!r} "
            f"lang={self.target_language!r}>"
        )
