"""Database repository layer for Correction operations."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.correction import Correction


class CorrectionRepository:
    """Async database operations for the Correction model."""

    @staticmethod
    async def create(db: AsyncSession, correction: Correction) -> Correction:
        """Persist a new Correction record."""
        db.add(correction)
        await db.commit()
        await db.refresh(correction)
        return correction

    @staticmethod
    async def bulk_create(db: AsyncSession, corrections: list[Correction]) -> list[Correction]:
        """Persist multiple Correction records in a single transaction."""
        for correction in corrections:
            db.add(correction)
        await db.commit()
        return corrections

    @staticmethod
    async def get_by_id(db: AsyncSession, correction_id: str) -> Correction | None:
        """Fetch a correction by primary key."""
        stmt = select(Correction).where(Correction.id == correction_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_for_event(
        db: AsyncSession,
        event_id: str,
        correction_type: str | None = None,
    ) -> Sequence[Correction]:
        """Get all corrections associated with an event."""
        stmt = select(Correction).where(Correction.event_id == event_id)
        if correction_type:
            stmt = stmt.where(Correction.correction_type == correction_type)
        stmt = stmt.order_by(Correction.detected_at.desc())
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def list_for_article(db: AsyncSession, article_id: str) -> Sequence[Correction]:
        """Get all corrections associated with a specific article."""
        stmt = (
            select(Correction)
            .where(Correction.article_id == article_id)
            .order_by(Correction.detected_at.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def count_for_event(db: AsyncSession, event_id: str) -> int:
        """Count total corrections found for an event."""
        from sqlalchemy import func
        stmt = select(func.count(Correction.id)).where(Correction.event_id == event_id)
        res = await db.execute(stmt)
        return res.scalar_one() or 0
