"""
End-to-end investigation pipeline runner for user-provided news article URL:
https://www.newindianexpress.com/galleries/2020/Feb/20/in-pics--ernakulam-bengaluru-ksrtc-bus-collides-with-lorry-in-tamil-nadu-19-dead-102768.html
"""
import asyncio
import json
import sys
from pathlib import Path

from app.db.session import get_session_factory, get_engine
from app.db.init_db import init_database
from app.orchestration.investigation_pipeline import InvestigationPipeline


async def main():
    target_url = "https://www.newindianexpress.com/galleries/2020/Feb/20/in-pics--ernakulam-bengaluru-ksrtc-bus-collides-with-lorry-in-tamil-nadu-19-dead-102768.html"
    print("==================================================")
    print("STARTING END-TO-END INVESTIGATION")
    print(f"Target URL: {target_url}")
    print("==================================================")

    engine = get_engine()
    await init_database(engine)

    factory = get_session_factory()
    async with factory() as db:
        pipeline = InvestigationPipeline()
        event, run_id = await pipeline.execute(db, seed_url=target_url)

        print("\n==================================================")
        print("PIPELINE EXECUTION COMPLETED")
        print("==================================================")
        print(f"Event ID:           {event.id}")
        print(f"Incident Type:      {event.incident_type}")
        print(f"Analysis Run ID:    {run_id}")
        print(f"Status:             {event.status}")

        from sqlalchemy import select
        from app.db.models.analysis_run import AnalysisRun
        res = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
        run = res.scalar_one_or_none()

        if run and run.result_summary_json:
            report_data = json.loads(run.result_summary_json)
            out_file = Path("data/investigation_report.json")
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\nReport saved to: {out_file.resolve()}")
            print(f"Timeline items: {len(report_data.get('timeline', []))}")
            print(f"Claim changes: {len(report_data.get('claim_changes', []))}")
            print(f"Internal inconsistencies: {len(report_data.get('internal_inconsistencies', []))}")
            print(f"Corrections detected: {len(report_data.get('corrections', []))}")
            print(f"Evidence chunks: {len(report_data.get('evidence', []))}")

if __name__ == "__main__":
    asyncio.run(main())
