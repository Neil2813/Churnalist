"""FastAPI endpoints for /api/v1/analysis."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import DBSession
from app.core.exceptions import AnalysisRunNotFoundError
from app.db.repositories.analysis_repository import AnalysisRepository
from app.orchestration.analysis_pipeline import AnalysisPipeline
from app.schemas.analysis import AnalysisRunRequest, AnalysisRunResponse
from app.schemas.reports import ReportResponse

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/run", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def trigger_analysis_run(db: DBSession, payload: AnalysisRunRequest) -> ReportResponse:
    """Trigger full DRIFT multi-agent analysis for an event and return the report."""
    pipeline = AnalysisPipeline()
    _run, report = await pipeline.execute(db, payload.event_id)
    return report


@router.get(
    "/runs/{run_id}",
    response_model=AnalysisRunResponse,
    summary="Get analysis run status (for polling)",
)
async def get_analysis_run(db: DBSession, run_id: str) -> AnalysisRunResponse:
    """
    Poll the status and progress of a running or completed analysis.
    """
    run = await AnalysisRepository.get_run_by_id(db, run_id)
    if not run:
        raise AnalysisRunNotFoundError(f"Analysis run '{run_id}' not found.")
    return AnalysisRunResponse.model_validate(run)


# Alias router for /analysis-runs/{run_id}
runs_router = APIRouter(tags=["Analysis"])


@runs_router.get(
    "/analysis-runs/{run_id}",
    response_model=AnalysisRunResponse,
    summary="Get analysis run status (for polling - alias endpoint)",
)
async def get_analysis_run_alias(db: DBSession, run_id: str) -> AnalysisRunResponse:
    """Poll status of an analysis run by run_id."""
    return await get_analysis_run(db, run_id)

