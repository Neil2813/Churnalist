"""
Database initialisation — creates tables and the FTS5 virtual table.

This runs at startup before requests are served.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import get_logger
from app.db.base import Base

logger = get_logger(__name__)


def _migrate_claims_schema(sync_conn) -> None:
    """Idempotently add multilingual columns to claims table if missing."""
    from sqlalchemy import inspect
    inspector = inspect(sync_conn)
    if "claims" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("claims")}
        new_columns = [
            ("original_language", "VARCHAR(16)"),
            ("original_text", "TEXT"),
            ("english_translation", "TEXT"),
            ("extracted_value", "TEXT"),
        ]
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                sync_conn.execute(text(f"ALTER TABLE claims ADD COLUMN {col_name} {col_type}"))
                logger.info("migrated_claims_column", column=col_name)


def _migrate_events_schema(sync_conn) -> None:
    """Idempotently add event context & search window columns to events table if missing."""
    from sqlalchemy import inspect
    inspector = inspect(sync_conn)
    if "events" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("events")}
        new_columns = [
            ("incident_type", "VARCHAR(256)"),
            ("anchor_timestamp", "TIMESTAMP"),
            ("search_window_start", "TIMESTAMP"),
            ("search_window_end", "TIMESTAMP"),
            ("locations_json", "TEXT"),
            ("countries_json", "TEXT"),
            ("organizations_json", "TEXT"),
            ("entities_json", "TEXT"),
        ]
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                sync_conn.execute(text(f"ALTER TABLE events ADD COLUMN {col_name} {col_type}"))
                logger.info("migrated_events_column", column=col_name)


def _migrate_runs_schema(sync_conn) -> None:
    """Idempotently add result_summary_json column to analysis_runs table if missing."""
    from sqlalchemy import inspect
    inspector = inspect(sync_conn)
    if "analysis_runs" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("analysis_runs")}
        if "result_summary_json" not in existing_cols:
            sync_conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN result_summary_json TEXT"))
            logger.info("migrated_analysis_runs_column", column="result_summary_json")


async def init_database(engine: AsyncEngine) -> None:
    """
    Create all SQLAlchemy tables (if they do not exist) and ensure the
    FTS5 virtual table is present.

    In production, use Alembic for schema management. This function is
    a convenience for the hackathon development workflow.
    """
    async with engine.begin() as conn:
        # Enable WAL mode and busy timeout for concurrent SQLite reads/writes
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA busy_timeout=30000;"))

        # Create all ORM-mapped tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("db_tables_created_or_verified")

        # Migrate claims, events, and runs tables for new columns if missing
        await conn.run_sync(_migrate_claims_schema)
        await conn.run_sync(_migrate_events_schema)
        await conn.run_sync(_migrate_runs_schema)

        # Create FTS5 virtual table for full-text search over articles
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts
            USING fts5(
                article_id UNINDEXED,
                title,
                content,
                language UNINDEXED,
                content='articles',
                content_rowid='rowid'
            )
        """))

        # Create FTS5 virtual table for claims
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts
            USING fts5(
                claim_id UNINDEXED,
                raw_text,
                subject,
                predicate,
                object_value,
                content='claims',
                content_rowid='rowid'
            )
        """))

        logger.info("fts5_tables_created_or_verified")


async def sync_article_fts(conn, article_id: str, title: str, content: str, language: str) -> None:
    """
    Insert or update a single article in the FTS5 index.
    Call this after inserting or updating an article.
    """
    await conn.execute(
        text("""
            INSERT OR REPLACE INTO articles_fts(article_id, title, content, language)
            VALUES (:article_id, :title, :content, :language)
        """),
        {"article_id": article_id, "title": title or "", "content": content or "", "language": language or ""},
    )


async def sync_claim_fts(
    conn,
    claim_id: str,
    raw_text: str,
    subject: str,
    predicate: str,
    object_value: str,
) -> None:
    """Insert or update a single claim in the FTS5 index."""
    await conn.execute(
        text("""
            INSERT OR REPLACE INTO claims_fts(claim_id, raw_text, subject, predicate, object_value)
            VALUES (:claim_id, :raw_text, :subject, :predicate, :object_value)
        """),
        {
            "claim_id": claim_id,
            "raw_text": raw_text or "",
            "subject": subject or "",
            "predicate": predicate or "",
            "object_value": object_value or "",
        },
    )
