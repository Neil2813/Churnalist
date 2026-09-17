"""FastAPI endpoints for /api/v1/provenance."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.provenance import ProvenanceGraphResponse
from app.services.provenance_service import ProvenanceService

router = APIRouter(prefix="/provenance", tags=["Provenance"])
provenance_service = ProvenanceService()


@router.get("/graph/{event_id}", response_model=ProvenanceGraphResponse)
async def get_provenance_graph(db: DBSession, event_id: str) -> ProvenanceGraphResponse:
    """Get provenance graph representation for visualization."""
    return await provenance_service.get_provenance_graph(db, event_id)
