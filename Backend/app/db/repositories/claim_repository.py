"""Database repository layer for Claim and ClaimRelation operations."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.claim import Claim
from app.db.models.claim_relation import ClaimRelation


class ClaimRepository:
    """Async database operations for Claim and ClaimRelation models."""

    @staticmethod
    async def create(db: AsyncSession, claim: Claim) -> Claim:
        """Persist a new Claim record."""
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        return claim

    @staticmethod
    async def bulk_create(db: AsyncSession, claims: list[Claim]) -> list[Claim]:
        """Persist multiple Claim records in a single transaction."""
        for claim in claims:
            db.add(claim)
        await db.commit()
        for claim in claims:
            await db.refresh(claim)
        return claims

    @staticmethod
    async def get_by_id(db: AsyncSession, claim_id: str) -> Claim | None:
        """Fetch claim by primary key with preloaded relations."""
        stmt = (
            select(Claim)
            .where(Claim.id == claim_id)
            .options(
                selectinload(Claim.source_relations),
                selectinload(Claim.target_relations),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_for_event(
        db: AsyncSession,
        event_id: str,
        claim_type: str | None = None,
    ) -> Sequence[Claim]:
        """Get all claims associated with an event, with optional type filter."""
        stmt = select(Claim).where(Claim.event_id == event_id)
        if claim_type:
            stmt = stmt.where(Claim.claim_type == claim_type)
        stmt = stmt.order_by(Claim.created_at)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def list_for_article(db: AsyncSession, article_id: str) -> Sequence[Claim]:
        """Get all claims belonging to an article."""
        stmt = select(Claim).where(Claim.article_id == article_id).order_by(Claim.source_start_offset)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_relation(db: AsyncSession, relation: ClaimRelation) -> ClaimRelation:
        """Persist a new ClaimRelation edge."""
        db.add(relation)
        await db.commit()
        await db.refresh(relation)
        return relation

    @staticmethod
    async def list_relations_for_event(
        db: AsyncSession,
        event_id: str,
        relation_type: str | None = None,
    ) -> Sequence[ClaimRelation]:
        """Get all drift relations for claims belonging to an event."""
        # Get claim IDs for the event first
        claim_ids_stmt = select(Claim.id).where(Claim.event_id == event_id)
        claim_ids_res = await db.execute(claim_ids_stmt)
        claim_ids = [row[0] for row in claim_ids_res.all()]

        if not claim_ids:
            return []

        stmt = select(ClaimRelation).where(
            ClaimRelation.source_claim_id.in_(claim_ids)
        )
        if relation_type:
            stmt = stmt.where(ClaimRelation.relation_type == relation_type)
        stmt = stmt.order_by(ClaimRelation.created_at)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def bulk_create_relations(db: AsyncSession, relations: list[ClaimRelation]) -> list[ClaimRelation]:
        """Persist multiple ClaimRelation records in a single transaction."""
        for rel in relations:
            db.add(rel)
        await db.commit()
        return relations
