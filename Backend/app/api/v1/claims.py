"""FastAPI endpoints for /api/v1/claims."""
from __future__ import annotations

from fastapi import APIRouter, Query, status
from typing import Any

from app.api.deps import DBSession
from app.schemas.claims import ClaimCreate, ClaimResponse, ClaimRelationResponse
from app.schemas.analysis import DriftMetricResponse
from app.services.claim_service import ClaimService
from app.db.repositories.claim_repository import ClaimRepository
from app.analysis.drift import compute_drift_summary

router = APIRouter(prefix="/claims", tags=["Claims"])
claim_service = ClaimService()


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(db: DBSession, payload: ClaimCreate) -> ClaimResponse:
    """Create a new extracted claim."""
    claim = await claim_service.create_claim(db, payload)
    return ClaimResponse.model_validate(claim)


@router.get("/event/{event_id}", response_model=list[ClaimResponse])
async def list_claims_for_event(db: DBSession, event_id: str) -> list[ClaimResponse]:
    """Get all extracted claims for an event."""
    claims = await claim_service.list_claims_for_event(db, event_id)
    return [ClaimResponse.model_validate(c) for c in claims]


@router.get("/event/{event_id}/relations", response_model=list[ClaimRelationResponse])
async def list_relations_for_event(db: DBSession, event_id: str) -> list[ClaimRelationResponse]:
    """Get all claim drift relations for an event."""
    relations = await claim_service.list_relations_for_event(db, event_id)
    return [ClaimRelationResponse.model_validate(r) for r in relations]


@router.get(
    "/event/{event_id}/drift",
    response_model=DriftMetricResponse,
    summary="Get drift summary metrics for an event",
)
async def get_drift_summary(db: DBSession, event_id: str) -> DriftMetricResponse:
    """
    Return aggregate drift metrics for all claims associated with an event.

    Summarises:
      - Total claims and relations detected
      - Number of drifting claims by category (numerical, severity, attribution, etc.)
    """
    claims = await ClaimRepository.list_for_event(db, event_id)
    relations = await ClaimRepository.list_relations_for_event(db, event_id)

    relation_dicts = [{"relation_type": r.relation_type} for r in relations]
    summary = compute_drift_summary(relation_dicts)

    return DriftMetricResponse(
        total_articles=0,  # populated by caller if needed
        total_claims=len(claims),
        drifting_claims_count=summary["drifting_count"],
        numerical_drifts_count=summary["numerical_drifts"],
        attribution_losses_count=summary["attribution_losses"],
        severity_changes_count=summary["severity_changes"],
        categories_breakdown=summary["categories_breakdown"],
    )
