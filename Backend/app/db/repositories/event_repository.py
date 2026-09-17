"""Database repository layer for Event operations."""
from __future__ import annotations

import hashlib
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import EventStatus
from app.db.models.event import Event


class EventRepository:
    """Async database operations for Event model."""

    @staticmethod
    async def create(db: AsyncSession, event: Event) -> Event:
        """Persist a new Event record."""
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_by_id(db: AsyncSession, event_id: str) -> Event | None:
        """Fetch event by primary key with preloaded articles."""
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(selectinload(Event.articles))
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_canonical_hash(db: AsyncSession, canonical_hash: str) -> Event | None:
        """Fetch event by deterministic canonical hash."""
        stmt = select(Event).where(Event.canonical_hash == canonical_hash)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_events(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status: EventStatus | None = None,
    ) -> Sequence[Event]:
        """List events with optional status filter and pagination."""
        stmt = select(Event).order_by(Event.created_at.desc())
        if status:
            stmt = stmt.where(Event.status == status)
        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def update_status(db: AsyncSession, event_id: str, status: EventStatus) -> Event | None:
        """Update event status field."""
        stmt = select(Event).where(Event.id == event_id)
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if event:
            event.status = status
            await db.commit()
            await db.refresh(event)
        return event

    @staticmethod
    def make_canonical_hash(title: str, location_name: str | None = None) -> str:
        """Generate deterministic SHA-256 canonical hash from event identity signals."""
        raw = f"{title.lower().strip()}|{(location_name or '').lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:64]
