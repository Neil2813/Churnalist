"""
Demo analysis runner.

Seeds demo data (if not already present) and runs the full DRIFT
analysis pipeline against the demo event, printing a summary of results.

Usage:
    python scripts/run_demo_analysis.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_demo() -> None:
    from app.db.init_db import init_db
    from app.db.session import get_async_session
    from app.orchestration.analysis_pipeline import AnalysisPipeline

    EVENT_ID = "evt_demo_001"

    print("🚀 DRIFT Demo Analysis Runner")
    print("=" * 50)

    # Ensure DB schema and seed data
    print("\n1️⃣  Initialising database...")
    await init_db()

    # Check event exists; if not, run seed script
    async for session in get_async_session():
        from sqlalchemy import select
        from app.db.models.event import Event

        result = await session.execute(select(Event).where(Event.id == EVENT_ID))
        event = result.scalar_one_or_none()

        if not event:
            print("   ⚠️  Demo event not found. Run seed_demo_data.py first:")
            print("       python scripts/seed_demo_data.py")
            return

        print(f"   ✅ Event found: {event.title}")

        # Run pipeline
        print("\n2️⃣  Running 5-agent DRIFT pipeline...")
        pipeline = AnalysisPipeline()

        try:
            run, report = await pipeline.execute(session, EVENT_ID)
        except Exception as exc:
            print(f"   ❌ Pipeline failed: {exc}")
            return

        print(f"\n3️⃣  Analysis complete (run_id: {run.id})")
        print("-" * 50)
        print(f"   Status:       {run.status}")
        print(f"   Articles:     {run.articles_processed}")
        print(f"   Claims:       {run.claims_processed}")
        print(f"   Relations:    {run.relations_created}")
        print(f"   Corrections:  {run.corrections_found}")

        if run.metrics_json:
            metrics = json.loads(run.metrics_json)
            elapsed = metrics.get("elapsed_seconds", 0)
            print(f"   Elapsed:      {elapsed:.1f}s")

        print("\n4️⃣  Report Summary")
        print("-" * 50)
        if hasattr(report, "headline"):
            print(f"   Headline:     {report.headline}")
            print(f"   Summary:      {report.summary[:120]}...")
            print(f"   Takeaway:     {report.reader_takeaway[:120]}...")
            if report.key_drifts:
                print(f"\n   Drift Items:  {len(report.key_drifts)} detected")
                for drift in report.key_drifts[:3]:
                    print(f"     • [{drift.category}] {drift.explanation[:80]}")

        print()
        print("✨ Done. Explore the API at http://localhost:8000/docs")
        break


if __name__ == "__main__":
    asyncio.run(run_demo())
