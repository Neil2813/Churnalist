"""
Analysis domain service orchestrating the DRIFT AI agent pipeline.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.claim_miner import ClaimMinerAgent
from app.agents.drift_investigator import DriftInvestigatorAgent
from app.agents.truth_trail import TruthTrailAgent
from app.core.constants import AnalysisStatus, PipelineStage
from app.db.models.analysis_run import AnalysisRun
from app.db.models.article import Article
from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation
from app.db.models.event import Event
from app.schemas.reports import ReportResponse


class AnalysisService:
    """Service orchestrating execution of DRIFT analysis pipeline."""

    def __init__(
        self,
        claim_miner: ClaimMinerAgent | None = None,
        drift_investigator: DriftInvestigatorAgent | None = None,
        truth_trail: TruthTrailAgent | None = None,
    ) -> None:
        self.claim_miner = claim_miner or ClaimMinerAgent()
        self.drift_investigator = drift_investigator or DriftInvestigatorAgent()
        self.truth_trail = truth_trail or TruthTrailAgent()

    async def run_event_analysis(
        self,
        db: AsyncSession,
        event_id: str,
    ) -> tuple[AnalysisRun, ReportResponse]:
        """Execute full 5-agent analysis pipeline for an event."""
        run = AnalysisRun(
            id=f"run_{uuid.uuid4().hex[:12]}",
            event_id=event_id,
            status=AnalysisStatus.RUNNING,
            current_stage=PipelineStage.CLAIM_MINING,
            started_at=datetime.utcnow(),
        )
        db.add(run)
        await db.commit()

        # Fetch Event and Articles
        event_q = await db.execute(select(Event).where(Event.id == event_id))
        event = event_q.scalar_one_or_none()

        articles_q = await db.execute(select(Article).where(Article.event_id == event_id))
        articles = list(articles_q.scalars().all())

        articles_dict = [
            {
                "id": a.id,
                "title": a.title or "",
                "content": a.content or "",
                "language": a.language or "en",
                "url": a.url,
            }
            for a in articles
        ]

        # Stage 1 & 2: Mine Claims
        all_claims: list[dict[str, Any]] = []
        for art in articles_dict:
            mined = await self.claim_miner.mine_claims(
                article_id=art["id"],
                event_id=event_id,
                title=art["title"],
                content=art["content"],
                language=art["language"],
            )
            all_claims.extend(mined)

            for c in mined:
                db_claim = Claim(
                    id=f"clm_{uuid.uuid4().hex[:12]}",
                    article_id=art["id"],
                    event_id=event_id,
                    claim_type=c["claim_type"],
                    subject=c["subject"],
                    predicate=c["predicate"],
                    object_value=c["object_value"],
                    object_unit=c.get("object_unit"),
                    raw_text=c["raw_text"],
                    source_start_offset=c.get("source_start_offset"),
                    source_end_offset=c.get("source_end_offset"),
                )
                db.add(db_claim)

        await db.commit()

        # Stage 3 & 4: Drift Investigation
        run.current_stage = PipelineStage.DRIFT_INVESTIGATION
        await db.commit()

        relations = []
        if len(articles_dict) >= 2:
            source_art_claims = [c for c in all_claims if c["article_id"] == articles_dict[0]["id"]]
            target_art_claims = [c for c in all_claims if c["article_id"] == articles_dict[1]["id"]]
            relations = await self.drift_investigator.investigate_claim_drift(
                source_claims=source_art_claims,
                target_claims=target_art_claims,
                source_lang=articles_dict[0]["language"],
                target_lang=articles_dict[1]["language"],
            )

        corrections = self.drift_investigator.track_corrections(event_id, articles_dict, all_claims)

        # Stage 5: Truth Trail Report Generation
        run.current_stage = PipelineStage.TRUTH_TRAIL
        await db.commit()

        event_info = {
            "id": event_id,
            "title": event.title if event else "News Event",
            "canonical_summary": event.canonical_summary if event else "",
        }

        report = await self.truth_trail.generate_provenance_report(
            event_info=event_info,
            articles=articles_dict,
            claims=all_claims,
            relations=relations,
            corrections=corrections,
        )

        run.status = AnalysisStatus.COMPLETED
        run.current_stage = PipelineStage.COMPLETED
        run.completed_at = datetime.utcnow()
        await db.commit()

        return run, report
