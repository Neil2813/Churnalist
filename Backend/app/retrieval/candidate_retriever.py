"""
Candidate Retriever combining FTS, temporal windows, and semantic search.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.article import Article
from app.retrieval.semantic_retriever import SemanticRetriever


class CandidateRetriever:
    """Retrieves candidate articles or claims matching event constraints."""

    def __init__(self, semantic_retriever: SemanticRetriever | None = None) -> None:
        self.semantic_retriever = semantic_retriever or SemanticRetriever()

    async def retrieve_candidate_articles(
        self,
        session: AsyncSession,
        keywords: list[str] | None = None,
        event_time: datetime | None = None,
        time_window_hours: int = 72,
        limit: int = 20,
    ) -> list[Article]:
        """Retrieve candidate articles from DB based on keyword matching and temporal proximity."""
        query = select(Article)

        filters = []
        if keywords:
            kw_filters = [
                or_(
                    Article.title.ilike(f"%{kw}%"),
                    Article.content.ilike(f"%{kw}%")
                )
                for kw in keywords
            ]
            filters.append(or_(*kw_filters))

        if event_time:
            start_time = event_time - timedelta(hours=time_window_hours)
            end_time = event_time + timedelta(hours=time_window_hours)
            filters.append(Article.published_at.between(start_time, end_time))

        if filters:
            query = query.where(*filters)

        query = query.limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())
