"""
Event domain service for managing event clusters.
"""
from __future__ import annotations

import uuid
from typing import Sequence
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EventStatus, TimePrecision
from app.core.exceptions import NotFoundError
from app.db.models.event import Event
from app.db.repositories.event_repository import EventRepository
from app.schemas.events import EventCreate, EventDiscoverRequest


class EventService:
    """Service layer for event CRUD and discovery handling."""

    async def create_event(self, db: AsyncSession, payload: EventCreate) -> Event:
        """Create a new Event."""
        canonical_hash = EventRepository.make_canonical_hash(
            payload.title, payload.location_name
        )
        # Return existing event if hash already present
        existing = await EventRepository.get_by_canonical_hash(db, canonical_hash)
        if existing:
            return existing

        event = Event(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            title=payload.title,
            canonical_summary=payload.canonical_summary,
            topic=payload.topic,
            location_name=payload.location_name,
            event_time=payload.event_time or datetime.utcnow(),
            time_precision=payload.time_precision,
            status=EventStatus.DISCOVERED,
            canonical_hash=canonical_hash,
        )
        return await EventRepository.create(db, event)

    async def get_event(self, db: AsyncSession, event_id: str) -> Event:
        """Fetch Event by ID or raise NotFoundError."""
        event = await EventRepository.get_by_id(db, event_id)
        if not event:
            raise NotFoundError(f"Event with ID '{event_id}' not found.")
        return event

    async def list_events(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status: EventStatus | None = None,
    ) -> Sequence[Event]:
        """List events with optional status filter."""
        return await EventRepository.list_events(db, skip=skip, limit=limit, status=status)

    async def discover_event(
        self,
        db: AsyncSession,
        payload: EventDiscoverRequest,
    ) -> Event:
        """
        Create an event from a seed URL or topic and enqueue article discovery.

        For the hackathon, this creates the event synchronously and returns it.
        Article ingestion from the seed URL fires as a background step in the
        ingestion orchestrator when a seed_url is provided.
        """
        # Derive a title from the seed URL domain or provided keywords
        if payload.seed_url:
            from urllib.parse import urlparse
            domain = urlparse(payload.seed_url).netloc or payload.seed_url
            title = f"Event from {domain}"
        elif payload.keywords:
            title = " ".join(payload.keywords[:6])
        elif payload.topic:
            title = payload.topic
        else:
            title = f"Discovered Event {uuid.uuid4().hex[:8]}"

        event = Event(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            title=title,
            topic=payload.topic,
            status=EventStatus.INGESTING,
            canonical_hash=EventRepository.make_canonical_hash(title),
            time_precision=TimePrecision.UNKNOWN,
        )

        # Avoid duplicate events for the same seed
        existing = await EventRepository.get_by_canonical_hash(db, event.canonical_hash)
        if existing:
            return existing

        created = await EventRepository.create(db, event)

        # Trigger live article discovery across news APIs & seed URL
        try:
            from app.agents.source_hunter import SourceHunterAgent
            hunter = SourceHunterAgent()
            kw = payload.keywords or ([payload.topic] if payload.topic else None)
            await hunter.discover_articles_for_event(
                db=db,
                event_id=created.id,
                seed_url=payload.seed_url,
                keywords=kw,
                max_articles=payload.max_articles or 10,
            )
        except Exception:
            pass  # Live fetch failure should not block event creation

        await EventRepository.update_status(db, created.id, EventStatus.READY)
        return created
