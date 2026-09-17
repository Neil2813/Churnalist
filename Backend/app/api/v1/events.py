"""FastAPI endpoints for /api/v1/events."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.deps import DBSession
from app.schemas.events import EventCreate, EventDiscoverRequest, EventResponse, EventDetailResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])
event_service = EventService()


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(db: DBSession, payload: EventCreate) -> EventResponse:
    """Create a new event cluster."""
    event = await event_service.create_event(db, payload)
    return EventResponse.model_validate(event)


@router.get("", response_model=list[EventResponse])
async def list_events(
    db: DBSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[EventResponse]:
    """List events."""
    events = await event_service.list_events(db, skip=skip, limit=limit)
    return [EventResponse.model_validate(e) for e in events]


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(db: DBSession, event_id: str) -> EventDetailResponse:
    """Get event details by ID."""
    event = await event_service.get_event(db, event_id)
    return EventDetailResponse.model_validate(event)


@router.post(
    "/discover",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Discover related multilingual articles for a seed URL or topic",
)
async def discover_event(
    payload: EventDiscoverRequest,
    db: DBSession,
) -> EventResponse:
    """
    Given a seed URL (or topic + keywords), discover related articles across
    specified languages and cluster them into an event.

    Returns the created or matched Event record. Article ingestion runs in
    the background; poll GET /events/{event_id} for updated article count.
    """
    event = await event_service.discover_event(db, payload)
    return EventResponse.model_validate(event)
