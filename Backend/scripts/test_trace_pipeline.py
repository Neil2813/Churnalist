"""
End-to-end verification script for Churnalist Trace a Story pipeline.
"""
import asyncio
from app.db.session import get_session_factory, get_engine
from app.db.init_db import init_database
from app.orchestration.investigation_pipeline import InvestigationPipeline


async def run_demo():
    engine = get_engine()
    await init_database(engine)

    seed_url = "https://en.wikipedia.org/wiki/2020_Avinashi_bus_accident"

    factory = get_session_factory()
    async with factory() as db:
        pipeline = InvestigationPipeline()
        event, run_id = await pipeline.execute(db, seed_url=seed_url)

        print("==================================================")
        print("INVESTIGATION COMPLETED SUCCESSFULLY!")
        print("==================================================")
        print(f"Event ID: {event.id}")
        print(f"Event Title: {event.title}")
        print(f"Incident Type: {event.incident_type}")
        print(f"Run ID: {run_id}")
        print(f"Status: {event.status}")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())
