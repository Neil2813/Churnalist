"""FastAPI routes for news sources and outlet management."""
from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import DBSession
from app.db.models.source import Source
from app.schemas.sources import SourceCreate, SourceResponse

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post(
    "",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new news source or publisher outlet",
)
async def create_source(
    payload: SourceCreate,
    db: DBSession,
) -> SourceResponse:
    """Register a publisher or wire agency source in the system."""
    source = Source(
        name=payload.name,
        domain=payload.domain,
        base_url=str(payload.base_url),
        source_type=payload.source_type.value if hasattr(payload.source_type, "value") else str(payload.source_type),
        language=payload.language,
        feed_url=str(payload.feed_url) if payload.feed_url else None,
        is_active=True,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.get(
    "",
    response_model=list[SourceResponse],
    summary="List active news sources",
)
async def list_sources(
    db: DBSession,
) -> list[SourceResponse]:
    """Retrieve all registered news sources."""
    stmt = select(Source).order_by(Source.name.asc())
    res = await db.execute(stmt)
    sources = res.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]
