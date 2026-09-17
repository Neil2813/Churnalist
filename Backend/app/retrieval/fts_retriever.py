"""
SQLite FTS5 lexical retriever for articles and claims.

FTS5 provides full-text search with BM25 ranking over article title,
content, and claim raw_text. This module manages both the FTS virtual
table and query execution.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FTS_TABLE, MAX_FTS_CANDIDATES
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── FTS5 table DDL ────────────────────────────────────────────────────────────

FTS_CREATE_SQL = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE}
USING fts5(
    article_id UNINDEXED,
    title,
    content,
    language UNINDEXED,
    tokenize = 'unicode61'
);
"""

FTS_CLAIM_TABLE = "claims_fts"
FTS_CLAIM_CREATE_SQL = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_CLAIM_TABLE}
USING fts5(
    claim_id UNINDEXED,
    article_id UNINDEXED,
    event_id UNINDEXED,
    raw_text,
    tokenize = 'unicode61'
);
"""


async def ensure_fts_tables(session: AsyncSession) -> None:
    """Create FTS5 virtual tables if they don't exist."""
    try:
        await session.execute(text(FTS_CREATE_SQL))
        await session.execute(text(FTS_CLAIM_CREATE_SQL))
        await session.commit()
        logger.info("fts_tables_ready")
    except Exception as exc:
        logger.warning("fts_table_creation_failed", error=str(exc))


async def index_article(
    session: AsyncSession,
    article_id: str,
    title: str,
    content: str,
    language: str,
) -> None:
    """Insert or replace an article's searchable text in the FTS index."""
    try:
        # Remove stale entry if exists
        await session.execute(
            text(f"DELETE FROM {FTS_TABLE} WHERE article_id = :article_id"),
            {"article_id": article_id},
        )
        await session.execute(
            text(
                f"INSERT INTO {FTS_TABLE}(article_id, title, content, language) "
                "VALUES (:article_id, :title, :content, :language)"
            ),
            {
                "article_id": article_id,
                "title": title or "",
                "content": (content or "")[:50_000],  # cap to avoid huge FTS entries
                "language": language or "en",
            },
        )
        await session.commit()
    except Exception as exc:
        logger.warning("fts_index_article_failed", article_id=article_id, error=str(exc))


async def index_claim(
    session: AsyncSession,
    claim_id: str,
    article_id: str,
    event_id: str,
    raw_text: str,
) -> None:
    """Insert or replace a claim's raw text in the claims FTS index."""
    try:
        await session.execute(
            text(f"DELETE FROM {FTS_CLAIM_TABLE} WHERE claim_id = :claim_id"),
            {"claim_id": claim_id},
        )
        await session.execute(
            text(
                f"INSERT INTO {FTS_CLAIM_TABLE}(claim_id, article_id, event_id, raw_text) "
                "VALUES (:claim_id, :article_id, :event_id, :raw_text)"
            ),
            {
                "claim_id": claim_id,
                "article_id": article_id,
                "event_id": event_id,
                "raw_text": raw_text or "",
            },
        )
        await session.commit()
    except Exception as exc:
        logger.warning("fts_index_claim_failed", claim_id=claim_id, error=str(exc))


async def fts_search_articles(
    session: AsyncSession,
    query: str,
    language: str | None = None,
    limit: int = MAX_FTS_CANDIDATES,
) -> list[dict[str, Any]]:
    """
    Run an FTS5 BM25 ranked query over article title and content.

    Returns a list of dicts: {article_id, title, rank}.
    """
    if not query or not query.strip():
        return []

    # Sanitize FTS5 query: escape special chars that would break the syntax
    fts_query = _sanitize_fts_query(query)

    try:
        if language:
            rows = await session.execute(
                text(
                    f"SELECT article_id, title, rank FROM {FTS_TABLE} "
                    f"WHERE {FTS_TABLE} MATCH :query AND language = :lang "
                    "ORDER BY rank LIMIT :limit"
                ),
                {"query": fts_query, "lang": language, "limit": limit},
            )
        else:
            rows = await session.execute(
                text(
                    f"SELECT article_id, title, rank FROM {FTS_TABLE} "
                    f"WHERE {FTS_TABLE} MATCH :query ORDER BY rank LIMIT :limit"
                ),
                {"query": fts_query, "limit": limit},
            )
        results = [
            {"article_id": row[0], "title": row[1], "fts_rank": abs(float(row[2]))}
            for row in rows.all()
        ]
        logger.debug("fts_search_articles", query=query, hits=len(results))
        return results
    except Exception as exc:
        logger.warning("fts_search_failed", query=query, error=str(exc))
        return []


async def fts_search_claims(
    session: AsyncSession,
    query: str,
    event_id: str | None = None,
    limit: int = MAX_FTS_CANDIDATES,
) -> list[dict[str, Any]]:
    """
    Run an FTS5 BM25 ranked query over claim raw_text.

    Returns a list of dicts: {claim_id, article_id, event_id, rank}.
    """
    if not query or not query.strip():
        return []

    fts_query = _sanitize_fts_query(query)

    try:
        if event_id:
            rows = await session.execute(
                text(
                    f"SELECT claim_id, article_id, event_id, rank FROM {FTS_CLAIM_TABLE} "
                    f"WHERE {FTS_CLAIM_TABLE} MATCH :query AND event_id = :event_id "
                    "ORDER BY rank LIMIT :limit"
                ),
                {"query": fts_query, "event_id": event_id, "limit": limit},
            )
        else:
            rows = await session.execute(
                text(
                    f"SELECT claim_id, article_id, event_id, rank FROM {FTS_CLAIM_TABLE} "
                    f"WHERE {FTS_CLAIM_TABLE} MATCH :query ORDER BY rank LIMIT :limit"
                ),
                {"query": fts_query, "limit": limit},
            )
        return [
            {
                "claim_id": row[0],
                "article_id": row[1],
                "event_id": row[2],
                "fts_rank": abs(float(row[3])),
            }
            for row in rows.all()
        ]
    except Exception as exc:
        logger.warning("fts_claim_search_failed", query=query, error=str(exc))
        return []


async def rebuild_fts_index(session: AsyncSession) -> int:
    """
    Rebuild the articles FTS index from scratch.

    Returns the count of articles indexed.
    """
    try:
        await session.execute(text(f"DELETE FROM {FTS_TABLE}"))
        result = await session.execute(
            text(
                f"INSERT INTO {FTS_TABLE}(article_id, title, content, language) "
                "SELECT id, COALESCE(title, ''), COALESCE(substr(content, 1, 50000), ''), "
                "COALESCE(language, 'en') FROM articles WHERE extraction_status != 'FAILED'"
            )
        )
        await session.commit()
        count = result.rowcount or 0
        logger.info("fts_rebuild_complete", articles_indexed=count)
        return count
    except Exception as exc:
        logger.error("fts_rebuild_failed", error=str(exc))
        return 0


def _sanitize_fts_query(query: str) -> str:
    """
    Sanitize user-supplied text for safe use in FTS5 MATCH expressions.

    Wraps the query in double-quotes for phrase matching. Strips characters
    that would break FTS5 syntax.
    """
    # Strip FTS5 special characters that can cause syntax errors
    safe = query.replace('"', ' ').replace("'", " ").strip()
    # Wrap in double quotes for implicit phrase matching
    return f'"{safe}"' if safe else ""
