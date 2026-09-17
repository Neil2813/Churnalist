"""FastAPI endpoints for /api/v1/corrections."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSession
from app.db.repositories.correction_repository import CorrectionRepository
from app.schemas.corrections import CorrectionResponse

router = APIRouter(prefix="/corrections", tags=["Corrections"])


@router.get(
    "/event/{event_id}",
    response_model=list[CorrectionResponse],
    summary="List detected corrections for an event",
)
async def list_corrections_for_event(
    db: DBSession,
    event_id: str,
) -> list[CorrectionResponse]:
    """
    Return all detected corrections, retractions, and clarifications for an event.

    Corrections are detected by the DriftInvestigator agent and represent
    cases where original claims appear to have been updated.
    """
    corrections = await CorrectionRepository.list_for_event(db, event_id)
    return [_to_response(c) for c in corrections]


def _to_response(c) -> CorrectionResponse:
    """Map ORM Correction to CorrectionResponse schema."""
    import json
    evidence = {}
    if c.evidence_json:
        try:
            evidence = json.loads(c.evidence_json)
        except Exception:
            pass

    surviving_ids: list[str] = evidence.get("surviving_article_ids", [])
    updated_ids: list[str] = evidence.get("updated_article_ids", [])

    return CorrectionResponse(
        id=c.id,
        event_id=c.event_id,
        article_id=c.article_id or "",
        original_claim_id=c.original_claim_id,
        corrected_claim_id=c.corrected_claim_id,
        correction_type=c.correction_type,
        original_text=c.original_claim_text or c.correction_text,
        corrected_text=c.corrected_claim_text or c.correction_text,
        correction_url=c.correction_url,
        outdated_articles_count=len(surviving_ids),
        outdated_article_ids=surviving_ids,
        detected_at=c.detected_at,
        created_at=c.detected_at,  # corrections use detected_at as creation time
    )
