"""Database repository layer for Article operations."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.article import Article, ArticleVersion


class ArticleRepository:
    """Async database operations for Article and ArticleVersion models."""

    @staticmethod
    async def get_by_id(db: AsyncSession, article_id: str) -> Article | None:
        """Fetch article by primary key with preloaded versions."""
        stmt = (
            select(Article)
            .where(Article.id == article_id)
            .options(selectinload(Article.versions))
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_url_hash(db: AsyncSession, url_hash: str) -> Article | None:
        """Fetch article by unique URL hash."""
        stmt = select(Article).where(Article.url_hash == url_hash)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_content_hash(db: AsyncSession, content_hash: str) -> Article | None:
        """Fetch article by body content hash."""
        stmt = select(Article).where(Article.content_hash == content_hash)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_articles(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        event_id: str | None = None,
        language: str | None = None,
        source_id: str | None = None,
    ) -> Sequence[Article]:
        """List articles with optional pagination and filtering."""
        stmt = select(Article).order_by(Article.created_at.desc())

        if event_id:
            stmt = stmt.where(Article.event_id == event_id)
        if language:
            stmt = stmt.where(Article.language == language)
        if source_id:
            stmt = stmt.where(Article.source_id == source_id)

        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def count_articles(
        db: AsyncSession,
        event_id: str | None = None,
        language: str | None = None,
    ) -> int:
        """Count total matching articles."""
        stmt = select(func.count(Article.id))
        if event_id:
            stmt = stmt.where(Article.event_id == event_id)
        if language:
            stmt = stmt.where(Article.language == language)

        res = await db.execute(stmt)
        return res.scalar_one() or 0
