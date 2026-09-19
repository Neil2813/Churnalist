"""
AnalysisPipeline — the five-agent orchestration coordinator.

Executes agents in sequence, updates progress via ProgressTracker,
persists results to DB using repositories, and handles errors without
exposing raw stack traces to callers.

Pipeline stages:
    1. SOURCE_HUNTING     — SourceHunterAgent: ingest + discover
    2. CLAIM_MINING       — ClaimMinerAgent: extract structured claims
    3. EVENT_WEAVING      — EventWeaverAgent: cluster + align claims
    4. DRIFT_INVESTIGATION — DriftInvestigatorAgent: drift + corrections
    5. TRUTH_TRAIL        — TruthTrailAgent: generate reader report
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.claim_miner import ClaimMinerAgent
from app.agents.drift_investigator import DriftInvestigatorAgent
from app.agents.event_weaver import EventWeaverAgent
from app.agents.source_hunter import SourceHunterAgent
from app.agents.truth_trail import TruthTrailAgent
from app.core.constants import AnalysisStatus, PipelineStage
from app.core.exceptions import AnalysisError
from app.core.logging import get_logger
from app.db.models.analysis_run import AnalysisRun
from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation
from app.db.models.correction import Correction
from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.repositories.claim_repository import ClaimRepository
from app.db.repositories.correction_repository import CorrectionRepository
from app.orchestration.pipeline_context import PipelineContext
from app.orchestration.progress import ProgressTracker
from app.schemas.reports import ReportResponse

logger = get_logger(__name__)


class AnalysisPipeline:
    """
    Orchestrates the full DRIFT five-agent analysis pipeline.

    Usage:
        pipeline = AnalysisPipeline()
        run, report = await pipeline.execute(db, event_id)
    """

    def __init__(
        self,
        source_hunter: SourceHunterAgent | None = None,
        claim_miner: ClaimMinerAgent | None = None,
        event_weaver: EventWeaverAgent | None = None,
        drift_investigator: DriftInvestigatorAgent | None = None,
        truth_trail: TruthTrailAgent | None = None,
    ) -> None:
        # Store as-is; agent instances are created lazily on first execute()
        self._source_hunter_arg = source_hunter
        self._claim_miner_arg = claim_miner
        self._event_weaver_arg = event_weaver
        self._drift_investigator_arg = drift_investigator
        self._truth_trail_arg = truth_trail

        # Will be populated on first call
        self._source_hunter: SourceHunterAgent | None = None
        self._claim_miner: ClaimMinerAgent | None = None
        self._event_weaver: EventWeaverAgent | None = None
        self._drift_investigator: DriftInvestigatorAgent | None = None
        self._truth_trail: TruthTrailAgent | None = None

    def _ensure_agents(self) -> None:
        """Lazy initialization of all agents on first pipeline call."""
        if self._source_hunter is None:
            self._source_hunter = self._source_hunter_arg or SourceHunterAgent()
        if self._claim_miner is None:
            self._claim_miner = self._claim_miner_arg or ClaimMinerAgent()
        if self._event_weaver is None:
            self._event_weaver = self._event_weaver_arg or EventWeaverAgent()
        if self._drift_investigator is None:
            self._drift_investigator = self._drift_investigator_arg or DriftInvestigatorAgent()
        if self._truth_trail is None:
            self._truth_trail = self._truth_trail_arg or TruthTrailAgent()

    async def execute(
        self,
        db: AsyncSession,
        event_id: str,
    ) -> tuple[AnalysisRun, ReportResponse]:
        """
        Create an AnalysisRun record and execute the full pipeline.

        Returns the final AnalysisRun and the generated ReportResponse.
        Raises AnalysisError on unrecoverable failures.
        """
        # Lazy init agents on first call
        self._ensure_agents()

        # ── Create run record ─────────────────────────────────────────────────
        run = AnalysisRun(
            id=f"run_{uuid.uuid4().hex[:12]}",
            event_id=event_id,
            status=AnalysisStatus.RUNNING,
            current_stage=PipelineStage.SOURCE_HUNTING,
            started_at=datetime.utcnow(),
            pipeline_version="1.0",
        )
        await AnalysisRepository.create_run(db, run)

        ctx = PipelineContext(
            run_id=run.id,
            event_id=event_id,
        )
        tracker = ProgressTracker(ctx, db)

        try:
            report = await self._run_stages(db, ctx, tracker)
        except Exception as exc:
            logger.error(
                "pipeline_unhandled_error",
                run_id=run.id,
                event_id=event_id,
                exc_info=exc,
            )
            await tracker.fail(
                error_code="ANALYSIS_FAILED",
                error_message=str(exc),
            )
            raise AnalysisError(f"Analysis pipeline failed: {exc}") from exc

        # Refresh run with final state
        final_run = await AnalysisRepository.get_run_by_id(db, run.id)
        return final_run or run, report

    async def _run_stages(
        self,
        db: AsyncSession,
        ctx: PipelineContext,
        tracker: ProgressTracker,
    ) -> ReportResponse:
        """Execute each pipeline stage in sequence."""

        # ── Stage 1: Source Hunter ────────────────────────────────────────────
        await tracker.enter_stage(PipelineStage.SOURCE_HUNTING)
        articles = await self._load_event_articles(db, ctx.event_id)
        ctx.article_ids = [a["id"] for a in articles]
        logger.info("source_hunter_done", run_id=ctx.run_id, articles=len(articles))

        # ── Stage 2: Claim Mining ─────────────────────────────────────────────
        await tracker.enter_stage(PipelineStage.CLAIM_MINING)
        all_raw_claims: list[dict[str, Any]] = []

        for art in articles:
            mined = await self._claim_miner.mine_claims(
                article_id=art["id"],
                event_id=ctx.event_id,
                title=art.get("title", ""),
                content=art.get("content", ""),
                language=art.get("language", "en"),
            )
            all_raw_claims.extend(mined)

            # Persist mined claims
            claim_models = [
                Claim(
                    id=f"clm_{uuid.uuid4().hex[:12]}",
                    article_id=art["id"],
                    event_id=ctx.event_id,
                    claim_type=c["claim_type"],
                    subject=c.get("subject"),
                    predicate=c.get("predicate"),
                    object_value=c.get("object_value"),
                    object_unit=c.get("object_unit"),
                    raw_text=c.get("raw_text"),
                    original_language=c.get("original_language"),
                    original_text=c.get("original_text"),
                    english_translation=c.get("english_translation"),
                    extracted_value=str(c.get("extracted_value")) if c.get("extracted_value") is not None else None,
                    source_start_offset=c.get("source_start_offset"),
                    source_end_offset=c.get("source_end_offset"),
                    attribution=c.get("attribution"),
                    certainty=c.get("certainty"),
                    severity=c.get("severity"),
                )
                for c in mined
            ]
            persisted = await ClaimRepository.bulk_create(db, claim_models)
            ctx.claim_ids.extend(p.id for p in persisted)

        ctx.raw_claims = all_raw_claims
        await tracker.update_counters(
            articles_processed=len(articles),
            claims_processed=len(all_raw_claims),
        )
        logger.info("claim_mining_done", run_id=ctx.run_id, claims=len(all_raw_claims))

        # ── Stage 3: Event Weaving ────────────────────────────────────────────
        await tracker.enter_stage(PipelineStage.EVENT_WEAVING)
        if len(articles) >= 2:
            aligned = await self._event_weaver.align_articles(
                event_id=ctx.event_id,
                articles=articles,
            )
            ctx.aligned_claim_groups = aligned
        logger.info("event_weaver_done", run_id=ctx.run_id, groups=len(ctx.aligned_claim_groups))

        # ── Stage 4: Drift Investigation ──────────────────────────────────────
        await tracker.enter_stage(PipelineStage.DRIFT_INVESTIGATION)
        relations: list[dict[str, Any]] = []
        corrections: list[dict[str, Any]] = []

        if len(articles) >= 2:
            src_claims = [c for c in all_raw_claims if c.get("article_id") == articles[0]["id"]]
            tgt_claims = [c for c in all_raw_claims if c.get("article_id") == articles[1]["id"]]

            relations = await self._drift_investigator.investigate_claim_drift(
                source_claims=src_claims,
                target_claims=tgt_claims,
                source_lang=articles[0].get("language", "en"),
                target_lang=articles[1].get("language", "en"),
            )
            corrections = self._drift_investigator.track_corrections(
                ctx.event_id, articles, all_raw_claims
            )

        ctx.raw_relations = relations
        ctx.raw_corrections = corrections

        # Persist relations
        relation_models: list[ClaimRelation] = []
        for rel in relations:
            if rel.get("source_claim_id") and rel.get("target_claim_id"):
                relation_models.append(
                    ClaimRelation(
                        id=f"rel_{uuid.uuid4().hex[:12]}",
                        source_claim_id=rel["source_claim_id"],
                        target_claim_id=rel["target_claim_id"],
                        relation_type=rel["relation_type"],
                        confidence=rel.get("confidence", 0.8),
                        reason=rel.get("reason"),
                        model_name=rel.get("model_name"),
                        prompt_version=rel.get("prompt_version"),
                    )
                )
        if relation_models:
            await ClaimRepository.bulk_create_relations(db, relation_models)
            ctx.relation_ids = [r.id for r in relation_models]

        # Persist corrections
        correction_models: list[Correction] = []
        for corr in corrections:
            correction_models.append(
                Correction(
                    id=f"cor_{uuid.uuid4().hex[:12]}",
                    event_id=ctx.event_id,
                    article_id=corr.get("article_id"),
                    correction_text=corr.get("correction_text", "Correction detected."),
                    correction_type=corr.get("correction_type", "OTHER"),
                    original_claim_text=corr.get("original_claim_text"),
                    corrected_claim_text=corr.get("corrected_claim_text"),
                    confidence=corr.get("confidence", 0.7),
                )
            )
        if correction_models:
            await CorrectionRepository.bulk_create(db, correction_models)
            ctx.correction_ids = [c.id for c in correction_models]

        await tracker.update_counters(
            relations_created=len(relation_models),
            corrections_found=len(correction_models),
        )
        logger.info(
            "drift_investigation_done",
            run_id=ctx.run_id,
            relations=len(relations),
            corrections=len(corrections),
        )

        # ── Stage 5: Truth Trail ──────────────────────────────────────────────
        await tracker.enter_stage(PipelineStage.TRUTH_TRAIL)

        event_info = await self._load_event_info(db, ctx.event_id)
        report = await self._truth_trail.generate_provenance_report(
            event_info=event_info,
            articles=articles,
            claims=all_raw_claims,
            relations=relations,
            corrections=corrections,
        )

        ctx.report = report if isinstance(report, dict) else report.model_dump()

        # ── Mark complete ─────────────────────────────────────────────────────
        await tracker.complete(metrics={
            "articles": len(articles),
            "claims": len(all_raw_claims),
            "relations": len(relations),
            "corrections": len(corrections),
            "elapsed_seconds": round(ctx.elapsed_seconds(), 2),
        })

        return report

    async def _load_event_articles(
        self,
        db: AsyncSession,
        event_id: str,
    ) -> list[dict[str, Any]]:
        """Load articles for an event as plain dicts (avoids lazy-load issues in async)."""
        from sqlalchemy import select
        from app.db.models.article import Article

        result = await db.execute(
            select(Article).where(Article.event_id == event_id)
        )
        articles = result.scalars().all()
        return [
            {
                "id": a.id,
                "title": a.title or "",
                "content": a.content or "",
                "language": a.language or "en",
                "url": a.url,
                "published_at": a.published_at,
                "source_type": a.source_type,
            }
            for a in articles
        ]

    async def _load_event_info(self, db: AsyncSession, event_id: str) -> dict[str, Any]:
        """Load event summary info as a plain dict."""
        from sqlalchemy import select
        from app.db.models.event import Event

        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            return {"id": event_id, "title": "News Event", "canonical_summary": ""}
        return {
            "id": event.id,
            "title": event.title,
            "canonical_summary": event.canonical_summary or "",
            "location_name": event.location_name,
            "event_time": event.event_time,
        }
