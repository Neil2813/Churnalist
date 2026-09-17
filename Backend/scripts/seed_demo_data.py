"""
Seed demo data script.

Creates a sample news source, event, and two articles (English + Hindi)
so the DRIFT API can be exercised immediately without external ingestion.

Usage:
    python scripts/seed_demo_data.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.init_db import init_db
from app.db.session import get_async_session


DEMO_SOURCE = {
    "id": "src_demo_wire_001",
    "name": "Demo Wire Service",
    "domain": "demowire.example.com",
    "base_url": "https://demowire.example.com",
    "source_type": "WIRE",
    "language": "en",
    "is_active": True,
}

DEMO_EVENT = {
    "id": "evt_demo_001",
    "title": "Factory Fire Injures Workers",
    "canonical_summary": "A fire broke out at an industrial facility injuring multiple workers.",
    "topic": "industrial_accident",
    "location_name": "Mumbai, India",
    "status": "READY",
    "canonical_hash": "demo_canonical_hash_factory_fire_001",
    "time_precision": "DAY",
}

DEMO_ARTICLES = [
    {
        "id": "art_demo_en_001",
        "event_id": "evt_demo_001",
        "source_id": "src_demo_wire_001",
        "url": "https://demowire.example.com/en/factory-fire",
        "canonical_url": "https://demowire.example.com/en/factory-fire",
        "url_hash": "demo_url_hash_en_001",
        "title": "Factory Fire Injures 17 Workers in Mumbai",
        "content": (
            "Officials confirmed that a fire broke out at an industrial factory in Mumbai on Thursday. "
            "Seventeen workers were injured, according to local authorities. "
            "The fire was brought under control after two hours. "
            "Police said the cause of the fire is under investigation."
        ),
        "language": "en",
        "language_confidence": 0.99,
        "source_type": "WIRE",
        "extraction_status": "FULL",
        "content_hash": "demo_content_hash_en_001",
    },
    {
        "id": "art_demo_hi_001",
        "event_id": "evt_demo_001",
        "source_id": "src_demo_wire_001",
        "url": "https://demowire.example.com/hi/factory-fire",
        "canonical_url": "https://demowire.example.com/hi/factory-fire",
        "url_hash": "demo_url_hash_hi_001",
        "title": "मुंबई में कारखाने में आग, 20 मजदूर गंभीर रूप से घायल",
        "content": (
            "मुंबई में एक औद्योगिक कारखाने में आग लग गई। "
            "अधिकारियों के अनुसार बीस मजदूर गंभीर रूप से घायल हो गए। "
            "आग दो घंटे बाद काबू में आई। "
            "पुलिस ने बताया कि आग के कारणों की जांच की जा रही है।"
        ),
        "language": "hi",
        "language_confidence": 0.97,
        "source_type": "WIRE",
        "extraction_status": "FULL",
        "content_hash": "demo_content_hash_hi_001",
    },
]


async def seed() -> None:
    """Insert demo seed data into the database."""
    from datetime import datetime
    from sqlalchemy import insert, select
    from app.db.models.source import Source
    from app.db.models.event import Event
    from app.db.models.article import Article

    print("🌱 Initialising database schema...")
    await init_db()

    async for session in get_async_session():
        # Source
        existing_src = await session.execute(
            select(Source).where(Source.id == DEMO_SOURCE["id"])
        )
        if not existing_src.scalar_one_or_none():
            session.add(Source(**DEMO_SOURCE))
            await session.commit()
            print(f"  ✅ Source created: {DEMO_SOURCE['name']}")
        else:
            print(f"  ⏭  Source already exists: {DEMO_SOURCE['name']}")

        # Event
        existing_evt = await session.execute(
            select(Event).where(Event.id == DEMO_EVENT["id"])
        )
        if not existing_evt.scalar_one_or_none():
            event_row = {**DEMO_EVENT, "event_time": datetime.utcnow()}
            session.add(Event(**event_row))
            await session.commit()
            print(f"  ✅ Event created: {DEMO_EVENT['title']}")
        else:
            print(f"  ⏭  Event already exists: {DEMO_EVENT['title']}")

        # Articles
        for art_data in DEMO_ARTICLES:
            existing_art = await session.execute(
                select(Article).where(Article.id == art_data["id"])
            )
            if not existing_art.scalar_one_or_none():
                art_row = {**art_data, "retrieved_at": datetime.utcnow()}
                session.add(Article(**art_row))
                await session.commit()
                print(f"  ✅ Article created: [{art_data['language']}] {art_data['title']}")
            else:
                print(f"  ⏭  Article already exists: {art_data['id']}")

        print()
        print("✨ Demo data seeded successfully.")
        print()
        print("Try these endpoints:")
        print("  GET  /api/v1/events")
        print("  GET  /api/v1/events/evt_demo_001")
        print("  GET  /api/v1/articles")
        print("  POST /api/v1/analysis/run  {\"event_id\": \"evt_demo_001\"}")
        break


if __name__ == "__main__":
    asyncio.run(seed())
