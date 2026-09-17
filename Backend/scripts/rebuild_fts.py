"""
FTS5 index rebuild script.

Drops and rebuilds the SQLite FTS5 virtual search tables from the current
articles and claims tables. Run this if the FTS index becomes stale or
after bulk data imports that bypassed the normal ingestion pipeline.

Usage:
    python scripts/rebuild_fts.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def rebuild() -> None:
    from app.db.init_db import init_db
    from app.db.session import get_async_session
    from app.retrieval.fts_retriever import (
        ensure_fts_tables,
        rebuild_fts_index,
        FTS_CLAIM_TABLE,
    )
    from sqlalchemy import text

    print("🔨 Initialising schema...")
    await init_db()

    async for session in get_async_session():
        # Ensure FTS tables exist
        print("📋 Creating FTS5 virtual tables (if not present)...")
        await ensure_fts_tables(session)

        # Rebuild articles FTS
        print("📰 Rebuilding articles_fts index...")
        count = await rebuild_fts_index(session)
        print(f"   ✅ {count} articles indexed.")

        # Rebuild claims FTS
        print("🔍 Rebuilding claims_fts index...")
        try:
            await session.execute(text(f"DELETE FROM {FTS_CLAIM_TABLE}"))
            result = await session.execute(
                text(
                    f"INSERT INTO {FTS_CLAIM_TABLE}(claim_id, article_id, event_id, raw_text) "
                    "SELECT id, article_id, COALESCE(event_id, ''), COALESCE(raw_text, '') "
                    "FROM claims WHERE raw_text IS NOT NULL AND raw_text != ''"
                )
            )
            await session.commit()
            claims_count = result.rowcount or 0
            print(f"   ✅ {claims_count} claims indexed.")
        except Exception as exc:
            print(f"   ⚠️  Claims FTS rebuild failed: {exc}")

        print()
        print("✨ FTS index rebuild complete.")
        break


if __name__ == "__main__":
    asyncio.run(rebuild())
