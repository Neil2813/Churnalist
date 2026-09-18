"""
ProgressTracker — updates analysis run progress in the database.

Called by the pipeline at the start and end of each stage so the
frontend can poll GET /analysis-runs/{run_id} to show live progress.
"""
from __future__ import annotations

from app.core.constants import AnalysisStatus, PipelineStage
from app.core.logging import get_logger
from app.db.repositories.analysis_repository import AnalysisRepository
from app.orchestration.pipeline_context import PipelineContext

logger = get_logger(__name__)

# ── Stage → progress percentage mapping ──────────────────────────────────────
# These are milestones; each stage updates the DB once on entry.
STAGE_PROGRESS: dict[PipelineStage, int] = {
    PipelineStage.SOURCE_HUNTING: 5,
    PipelineStage.CLAIM_MINING: 25,
    PipelineStage.EVENT_WEAVING: 50,
    PipelineStage.DRIFT_INVESTIGATION: 70,
    PipelineStage.TRUTH_TRAIL: 90,
    PipelineStage.COMPLETED: 100,
}


class ProgressTracker:
    """
    Writes AnalysisRun progress updates to the database.

    Pipeline stages call `enter_stage()` at the beginning of each phase
    and `complete()` or `fail()` at the end of the pipeline.
    """

    def __init__(self, context: PipelineContext, db) -> None:
        self._ctx = context
        self._db = db

    async def enter_stage(self, stage: PipelineStage) -> None:
        """Record that we have entered a new pipeline stage."""
        progress = STAGE_PROGRESS.get(stage, self._ctx.progress_pct)
        self._ctx.current_stage = stage
        self._ctx.progress_pct = progress

        await AnalysisRepository.update_run_progress(
            self._db,
            self._ctx.run_id,
            status=AnalysisStatus.RUNNING,
            stage=stage,
            progress=progress,
        )
        logger.info(
            "pipeline_stage_entered",
            run_id=self._ctx.run_id,
            stage=stage,
            progress=progress,
        )

    async def update_counters(
        self,
        *,
        articles_processed: int | None = None,
        claims_processed: int | None = None,
        relations_created: int | None = None,
        corrections_found: int | None = None,
    ) -> None:
        """Update processed-item counters on the AnalysisRun record."""
        await AnalysisRepository.update_run_progress(
            self._db,
            self._ctx.run_id,
            articles_processed=articles_processed,
            claims_processed=claims_processed,
            relations_created=relations_created,
            corrections_found=corrections_found,
        )

    async def complete(self, metrics: dict | None = None) -> None:
        """Mark the pipeline as COMPLETED with final metrics."""
        from datetime import datetime
        self._ctx.completed_at = datetime.utcnow()
        self._ctx.current_stage = PipelineStage.COMPLETED
        self._ctx.progress_pct = 100

        await AnalysisRepository.update_run_progress(
            self._db,
            self._ctx.run_id,
            status=AnalysisStatus.COMPLETED,
            stage=PipelineStage.COMPLETED,
            progress=100,
            articles_processed=len(self._ctx.article_ids),
            claims_processed=len(self._ctx.claim_ids),
            relations_created=len(self._ctx.relation_ids),
            corrections_found=len(self._ctx.correction_ids),
            metrics=metrics or self._ctx.metrics,
        )
        logger.info(
            "pipeline_completed",
            run_id=self._ctx.run_id,
            elapsed=self._ctx.elapsed_seconds(),
        )

    async def fail(self, error_code: str, error_message: str) -> None:
        """Mark the pipeline as FAILED with error details."""
        from datetime import datetime
        self._ctx.completed_at = datetime.utcnow()
        self._ctx.error = error_message

        await AnalysisRepository.update_run_progress(
            self._db,
            self._ctx.run_id,
            status=AnalysisStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
        )
        logger.error(
            "pipeline_failed",
            run_id=self._ctx.run_id,
            error_code=error_code,
            error_message=error_message,
        )
