"""SearchResult ORM model for storing discovery provenance."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class SearchResult(Base, UUIDMixin, TimestampMixin):
    """
    Persisted search result item returned from SerpAPI / DuckDuckGo discovery.
    Search results are persisted because discovery itself is part of story provenance.
    """
    __tablename__ = "search_results"

    event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=True, index=True
    )
    run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    search_query: Mapped[str] = mapped_column(Text, nullable=False)
    engine: Mapped[str] = mapped_column(String(64), nullable=False, default="duckduckgo")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="serpapi")

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    raw_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SearchResult query={self.search_query!r} url={self.url!r}>"
