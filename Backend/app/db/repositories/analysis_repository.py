"""Database repository layer for AnalysisRun operations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AnalysisStatus, PipelineStage
from app.db.models.analysis_run import AnalysisRun


class AnalysisRepository:
    """Async database operations for AnalysisRun model."""

    @staticmethod
    async def create_run(db: AsyncSession, run: AnalysisRun) -> AnalysisRun:
        """Persist a new AnalysisRun record."""
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def get_run_by_id(db: AsyncSession, run_id: str) -> AnalysisRun | None:
        """Fetch an analysis run by primary key."""
        stmt = select(AnalysisRun).where(AnalysisRun.id == run_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_run_progress(
        db: AsyncSession,
        run_id: str,
        *,
        status: AnalysisStatus | None = None,
        stage: PipelineStage | None = None,
        progress: int | None = None,
        articles_processed: int | None = None,
        claims_processed: int | None = None,
        relations_created: int | None = None,
        corrections_found: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> AnalysisRun | None:
        """Update mutable progress fields on an AnalysisRun."""
        import json
        stmt = select(AnalysisRun).where(AnalysisRun.id == run_id)
        res = await db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            return None

        if status is not None:
            run.status = status
            if status in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED):
                run.completed_at = datetime.utcnow()
        if stage is not None:
            run.current_stage = stage
        if progress is not None:
            run.progress = max(0, min(100, progress))
        if articles_processed is not None:
            run.articles_processed = articles_processed
        if claims_processed is not None:
            run.claims_processed = claims_processed
        if relations_created is not None:
            run.relations_created = relations_created
        if corrections_found is not None:
            run.corrections_found = corrections_found
        if error_code is not None:
            run.error_code = error_code
        if error_message is not None:
            run.error_message = error_message
        if metrics is not None:
            run.metrics_json = json.dumps(metrics)

        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def list_runs_for_event(
        db: AsyncSession,
        event_id: str,
        limit: int = 10,
    ) -> Sequence[AnalysisRun]:
        """List analysis runs for an event, most recent first."""
        stmt = (
            select(AnalysisRun)
            .where(AnalysisRun.event_id == event_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return res.scalars().all()
