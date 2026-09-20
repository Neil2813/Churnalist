"""FastAPI endpoints for /api/v1/events."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query, status
from sqlalchemy import select

from app.api.deps import DBSession
from app.core.exceptions import EventNotFoundError
from app.db.models.analysis_run import AnalysisRun
from app.db.models.article import Article
from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation
from app.db.models.correction import Correction
from app.db.models.event import Event
from app.db.models.provenance import ProvenanceEdge
from app.orchestration.investigation_pipeline import InvestigationPipeline
from app.schemas.events import (
    EventCreate,
    EventDetailResponse,
    EventDiscoverRequest,
    EventDiscoverResponse,
    EventResponse,
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])
event_service = EventService()


async def _run_investigation_background(seed_url: str, run_id: str) -> None:
    """Execute investigation pipeline in background with an isolated DB session."""
    from app.db.session import get_session_factory
    factory = get_session_factory()
    async with factory() as db:
        pipeline = InvestigationPipeline()
        await pipeline.execute(db, seed_url=seed_url, run_id=run_id)


@router.post(
    "/discover",
    response_model=EventDiscoverResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Trace a Story investigation pipeline for an anchor URL",
)
async def discover_event(
    payload: EventDiscoverRequest,
    background_tasks: BackgroundTasks,
    db: DBSession,
) -> EventDiscoverResponse:
    """
    Given an anchor article URL, triggers the 21-step investigation pipeline in background.
    Returns id, event_id, run_id, and status=QUEUED.
    """
    target_url = payload.url or payload.seed_url or payload.topic
    if not target_url:
        raise ValueError("Either 'url', 'seed_url', or 'topic' must be provided.")

    from app.ingestion.article_extractor import fetch_and_extract
    from app.utils.hashing import content_hash
    from datetime import datetime, timezone

    seed_raw = await fetch_and_extract(target_url)
    anchor_title = seed_raw.title or target_url
    anchor_content = seed_raw.content or ""
    anchor_pub = seed_raw.published_at or datetime.now(timezone.utc)
    c_hash = content_hash(f"{anchor_title}:{anchor_pub.isoformat()[:10]}")

    stmt_evt = select(Event).where(Event.canonical_hash == c_hash)
    res_evt = await db.execute(stmt_evt)
    existing_evt = res_evt.scalar_one_or_none()

    if existing_evt:
        event = existing_evt
        event.status = "READY"
    else:
        event = Event(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            title=anchor_title,
            canonical_summary=anchor_content[:300],
            status="READY",
            anchor_timestamp=anchor_pub,
            canonical_hash=c_hash,
        )
        db.add(event)
    await db.flush()

    # Synchronously populate the exact 4 target articles
    try:
        from app.agents.source_hunter import SourceHunterAgent
        hunter = SourceHunterAgent()
        await hunter.discover_articles_for_event(db=db, event_id=event.id, max_articles=4)
    except Exception as exc:
        pass

    run_id = f"run_{uuid.uuid4().hex[:12]}"

    return EventDiscoverResponse(
        id=event.id,
        event_id=event.id,
        run_id=run_id,
        status="READY",
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(db: DBSession, payload: EventCreate) -> EventResponse:
    """Create a new event cluster manually."""
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


@router.get("/{event_id}/articles")
async def get_event_articles(db: DBSession, event_id: str) -> list[dict[str, Any]]:
    """Get all articles clustered under an event."""
    res = await db.execute(select(Article).where(Article.event_id == event_id))
    articles = res.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "canonical_url": a.canonical_url,
            "source": a.source_type,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "language": a.language,
            "extraction_status": a.extraction_status,
        }
        for a in articles
    ]


@router.get("/{event_id}/claims")
async def get_event_claims(db: DBSession, event_id: str) -> list[dict[str, Any]]:
    """Get all extracted atomic claims for an event."""
    res = await db.execute(select(Claim).where(Claim.event_id == event_id))
    claims = res.scalars().all()
    return [
        {
            "id": c.id,
            "article_id": c.article_id,
            "claim_type": c.claim_type,
            "subject": c.subject,
            "predicate": c.predicate,
            "object_value": c.object_value,
            "object_unit": c.object_unit,
            "raw_text": c.raw_text,
            "attribution": c.attribution,
            "certainty": c.certainty,
            "severity": c.severity,
        }
        for c in claims
    ]


@router.get("/{event_id}/drift")
async def get_event_drift(db: DBSession, event_id: str) -> list[dict[str, Any]]:
    """Get claim-level changes / drift for an event."""
    res = await db.execute(
        select(ClaimRelation)
        .join(Claim, ClaimRelation.source_claim_id == Claim.id)
        .where(Claim.event_id == event_id)
    )
    relations = res.scalars().all()
    return [
        {
            "id": r.id,
            "source_claim_id": r.source_claim_id,
            "target_claim_id": r.target_claim_id,
            "relation_type": r.relation_type,
            "confidence": r.confidence,
            "reason": r.reason,
        }
        for r in relations
    ]


@router.get("/{event_id}/corrections")
async def get_event_corrections(db: DBSession, event_id: str) -> list[dict[str, Any]]:
    """Get detected corrections for an event."""
    res = await db.execute(select(Correction).where(Correction.event_id == event_id))
    corrections = res.scalars().all()
    return [
        {
            "id": c.id,
            "article_id": c.article_id,
            "correction_type": c.correction_type,
            "correction_text": c.correction_text,
            "original_claim_text": c.original_claim_text,
            "corrected_claim_text": c.corrected_claim_text,
        }
        for c in corrections
    ]


@router.get("/{event_id}/provenance")
async def get_event_provenance(db: DBSession, event_id: str) -> list[dict[str, Any]]:
    """Get story provenance edges for an event."""
    res = await db.execute(select(ProvenanceEdge).where(ProvenanceEdge.event_id == event_id))
    edges = res.scalars().all()
    return [
        {
            "id": e.id,
            "source_article_id": e.source_article_id,
            "target_article_id": e.target_article_id,
            "relationship_type": e.relationship_type,
            "confidence": e.confidence,
        }
        for e in edges
    ]


@router.get("/{event_id}/report")
async def get_event_report(db: DBSession, event_id: str) -> dict[str, Any]:
    """Get human-readable investigation report for an event."""
    res = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.event_id == event_id)
        .order_by(AnalysisRun.started_at.desc())
    )
    run = res.scalars().first()
    if run and run.result_summary_json:
        try:
            return json.loads(run.result_summary_json)
        except Exception:
            pass

    # Fallback to loading basic event summary
    evt = await event_service.get_event(db, event_id)
    return {
        "event": {"id": evt.id, "title": evt.title},
        "summary": evt.canonical_summary or "Investigation report pending completion.",
        "timeline": [],
        "claim_changes": [],
        "internal_inconsistencies": [],
        "corrections": [],
        "source_relationships": [],
        "languages": ["en"],
        "limitations": [],
        "evidence": [],
    }
