"""
Claim domain service for claim persistence and querying.
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation
from app.schemas.claims import ClaimCreate


class ClaimService:
    """Service layer for claims and claim relations."""

    async def create_claim(self, db: AsyncSession, payload: ClaimCreate) -> Claim:
        """Create a new Claim record."""
        claim = Claim(
            id=f"clm_{uuid.uuid4().hex[:12]}",
            article_id=payload.article_id,
            event_id=payload.event_id,
            claim_type=payload.claim_type,
            subject=payload.subject,
            predicate=payload.predicate,
            object_value=payload.object_value,
            object_unit=payload.object_unit,
            location=payload.location,
            event_time=str(payload.event_time) if payload.event_time else None,
            attribution=payload.attribution,
            certainty=payload.certainty,
            modality=payload.modality,
            severity=payload.severity,
            raw_text=payload.raw_text,
            source_start_offset=payload.source_start_offset,
            source_end_offset=payload.source_end_offset,
        )
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        return claim

    async def get_claim(self, db: AsyncSession, claim_id: str) -> Claim:
        """Fetch Claim by ID or raise NotFoundError."""
        query = select(Claim).where(Claim.id == claim_id)
        res = await db.execute(query)
        claim = res.scalar_one_or_none()
        if not claim:
            raise NotFoundError(f"Claim with ID '{claim_id}' not found.")
        return claim

    async def list_claims_for_event(self, db: AsyncSession, event_id: str) -> Sequence[Claim]:
        """Get all claims for an event."""
        query = select(Claim).where(Claim.event_id == event_id)
        res = await db.execute(query)
        return res.scalars().all()

    async def list_relations_for_event(self, db: AsyncSession, event_id: str) -> Sequence[ClaimRelation]:
        """Get all claim relations for claims belonging to event."""
        claims = await self.list_claims_for_event(db, event_id)
        claim_ids = [c.id for c in claims]
        if not claim_ids:
            return []
        query = select(ClaimRelation).where(ClaimRelation.source_claim_id.in_(claim_ids))
        res = await db.execute(query)
        return res.scalars().all()
