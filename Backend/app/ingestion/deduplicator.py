"""Deduplication and versioning engine for ingested articles."""
from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.article import Article
from app.utils.hashing import hash_content, hash_url


class DeduplicationAction(str, Enum):
    NEW_ARTICLE = "NEW_ARTICLE"
    SKIP_DUPLICATE = "SKIP_DUPLICATE"
    NEW_VERSION = "NEW_VERSION"
    SYNDICATED_COPY = "SYNDICATED_COPY"


class DeduplicationResult(NamedTuple):
    action: DeduplicationAction
    existing_article: Article | None
    url_hash: str
    content_hash: str


class Deduplicator:
    """
    Checks incoming article against stored DB records by URL hash and content hash.
    Enforces uniqueness invariants and triggers content versioning on updates.
    """

    @staticmethod
    async def evaluate(
        db: AsyncSession,
        url: str,
        content: str,
    ) -> DeduplicationResult:
        """
        Evaluate an incoming URL and content against DB articles.
        Returns the action decision and existing article record if any.
        """
        url_hash = hash_url(url)
        content_hash = hash_content(content) if content else ""

        # 1. Search DB for matching url_hash
        stmt_url = select(Article).where(Article.url_hash == url_hash)
        res_url = await db.execute(stmt_url)
        article_by_url = res_url.scalar_one_or_none()

        if article_by_url:
            # Check if content has changed
            if article_by_url.content_hash == content_hash:
                return DeduplicationResult(
                    action=DeduplicationAction.SKIP_DUPLICATE,
                    existing_article=article_by_url,
                    url_hash=url_hash,
                    content_hash=content_hash,
                )
            else:
                return DeduplicationResult(
                    action=DeduplicationAction.NEW_VERSION,
                    existing_article=article_by_url,
                    url_hash=url_hash,
                    content_hash=content_hash,
                )

        # 2. Search DB for matching content_hash (different URL, identical body)
        if content_hash:
            stmt_content = select(Article).where(Article.content_hash == content_hash)
            res_content = await db.execute(stmt_content)
            article_by_content = res_content.scalar_one_or_none()

            if article_by_content:
                return DeduplicationResult(
                    action=DeduplicationAction.SYNDICATED_COPY,
                    existing_article=article_by_content,
                    url_hash=url_hash,
                    content_hash=content_hash,
                )

        # 3. Completely new article
        return DeduplicationResult(
            action=DeduplicationAction.NEW_ARTICLE,
            existing_article=None,
            url_hash=url_hash,
            content_hash=content_hash,
        )
