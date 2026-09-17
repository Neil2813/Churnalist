"""
Provenance service for constructing article and claim provenance graphs.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProvenanceRelation
from app.db.models.article import Article
from app.db.models.event import Event
from app.db.models.provenance import ProvenanceEdge
from app.schemas.provenance import (
    ProvenanceGraphResponse,
    ProvenanceGraphNode,
    ProvenanceEdgeResponse,
)


class ProvenanceService:
    """Service layer for provenance graph operations."""

    async def get_provenance_graph(
        self, db: AsyncSession, event_id: str
    ) -> ProvenanceGraphResponse:
        """Construct full provenance graph for an event."""
        articles_q = await db.execute(select(Article).where(Article.event_id == event_id))
        articles = list(articles_q.scalars().all())

        nodes: list[ProvenanceGraphNode] = []
        edges: list[ProvenanceEdgeResponse] = []

        for art in articles:
            nodes.append(
                ProvenanceGraphNode(
                    id=art.id,
                    label=art.title or "Article",
                    node_type="ARTICLE",
                    language=art.language,
                    url=art.url,
                )
            )

        # Connect articles in chain for visualization
        for i in range(len(articles) - 1):
            src_art = articles[i]
            tgt_art = articles[i + 1]
            rel = ProvenanceRelation.TRANSLATED_TO if src_art.language != tgt_art.language else ProvenanceRelation.REWRITTEN_TO
            edges.append(
                ProvenanceEdgeResponse(
                    id=f"pedg_{uuid.uuid4().hex[:12]}",
                    event_id=event_id,
                    from_type="ARTICLE",
                    from_id=src_art.id,
                    to_type="ARTICLE",
                    to_id=tgt_art.id,
                    relation=rel,
                    confidence=0.90,
                    created_at=datetime.utcnow(),
                )
            )

        return ProvenanceGraphResponse(
            event_id=event_id,
            nodes=nodes,
            edges=edges,
        )
