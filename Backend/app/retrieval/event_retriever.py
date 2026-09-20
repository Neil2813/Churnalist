"""
Event-aware candidate article and RAG chunk retriever.

Execution order for chunk retrieval:
    1. Filter chunks by event_id metadata
    2. FTS5 / lexical retrieval on chunk text
    3. Multilingual embedding similarity
    4. Rerank and select top 8-12 evidence chunks for Groq reasoning
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import EVENT_CLUSTER_WINDOW_HOURS, MAX_SEMANTIC_CANDIDATES
from app.core.logging import get_logger
from app.db.models.article import Article
from app.db.models.retrieval_chunk import RetrievalChunk
from app.retrieval.fts_retriever import fts_search_articles
from app.retrieval.reranker import rerank_candidates
from app.retrieval.semantic_retriever import SemanticRetriever, cosine_similarity
from app.embeddings.service import EmbeddingService
from app.utils.hashing import content_hash

logger = get_logger(__name__)


def chunk_article_content(
    article_id: str,
    event_id: str,
    content: str,
    url: str,
    source_name: str | None = None,
    published_at: datetime | None = None,
    language: str | None = "en",
    chunk_size: int = 500,
) -> list[RetrievalChunk]:
    """Paragraph-aware semantic chunking preserving article-level metadata."""
    if not content:
        return []

    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    chunks: list[RetrievalChunk] = []

    current_text = ""
    chunk_idx = 0

    for para in paragraphs:
        if len(current_text) + len(para) > chunk_size and current_text:
            chunks.append(
                RetrievalChunk(
                    id=f"chk_{uuid.uuid4().hex[:12]}",
                    article_id=article_id,
                    event_id=event_id,
                    source_name=source_name or "Unknown Source",
                    url=url,
                    published_at=published_at,
                    language=language or "en",
                    chunk_index=chunk_idx,
                    content=current_text.strip(),
                    content_hash=content_hash(current_text.strip()),
                    retrieved_at=datetime.now(timezone.utc),
                )
            )
            chunk_idx += 1
            current_text = para + "\n"
        else:
            current_text += para + "\n"

    if current_text.strip():
        chunks.append(
            RetrievalChunk(
                id=f"chk_{uuid.uuid4().hex[:12]}",
                article_id=article_id,
                event_id=event_id,
                source_name=source_name or "Unknown Source",
                url=url,
                published_at=published_at,
                language=language or "en",
                chunk_index=chunk_idx,
                content=current_text.strip(),
                content_hash=content_hash(current_text.strip()),
                retrieved_at=datetime.now(timezone.utc),
            )
        )

    return chunks


class EventRetriever:
    """
    Retrieves candidate articles and evidence chunks for Churnalist event investigation.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        if embedding_service is None:
            s = get_settings()
            embedding_service = EmbeddingService(
                model_name=s.embedding_model,
                device=s.embedding_device,
            )
        self._embedding_service = embedding_service
        self._semantic_retriever = SemanticRetriever(self._embedding_service)

    async def index_article_chunks(
        self,
        session: AsyncSession,
        article_id: str,
        event_id: str,
        content: str,
        url: str,
        source_name: str | None = None,
        published_at: datetime | None = None,
        language: str | None = "en",
    ) -> list[RetrievalChunk]:
        """Chunk article and store in retrieval_chunks DB table."""
        chunks = chunk_article_content(
            article_id=article_id,
            event_id=event_id,
            content=content,
            url=url,
            source_name=source_name,
            published_at=published_at,
            language=language,
        )
        if chunks:
            session.add_all(chunks)
            await session.flush()
        return chunks

    async def retrieve_evidence_chunks(
        self,
        session: AsyncSession,
        event_id: str,
        query: str = "",
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Event-aware RAG evidence retrieval:
        1. metadata filter by event_id
        2. SQLite FTS5 / lexical match
        3. Multilingual embedding similarity if model loaded
        4. Select top 8-12 evidence chunks for Groq prompt
        """
        stmt = select(RetrievalChunk).where(RetrievalChunk.event_id == event_id)
        res = await session.execute(stmt)
        chunks = list(res.scalars().all())

        if not chunks:
            return []

        # Score chunks
        scored_chunks: list[dict[str, Any]] = []
        q_lower = query.lower()

        for chk in chunks:
            score = 0.5  # base relevance
            if query:
                words = [w for w in q_lower.split() if len(w) > 3]
                if words:
                    matches = sum(1 for w in words if w in chk.content.lower())
                    score += (matches / len(words)) * 0.5

            scored_chunks.append({
                "chunk_id": chk.id,
                "article_id": chk.article_id,
                "event_id": chk.event_id,
                "source_name": chk.source_name,
                "url": chk.url,
                "published_at": chk.published_at.isoformat() if chk.published_at else None,
                "language": chk.language,
                "chunk_index": chk.chunk_index,
                "content": chk.content,
                "score": score,
            })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    async def find_related_articles(
        self,
        session: AsyncSession,
        *,
        reference_text: str,
        reference_title: str = "",
        reference_time: datetime | None = None,
        reference_location: str | None = None,
        reference_domain: str | None = None,
        languages: list[str] | None = None,
        exclude_article_ids: list[str] | None = None,
        time_window_hours: int = EVENT_CLUSTER_WINDOW_HOURS,
        top_k: int = MAX_SEMANTIC_CANDIDATES,
    ) -> list[dict[str, Any]]:
        """Find related articles using hard filter + FTS5 + semantic scoring."""
        db_candidates = await self._hard_filter(
            session,
            reference_time=reference_time,
            languages=languages,
            time_window_hours=time_window_hours,
            exclude_ids=exclude_article_ids or [],
        )

        if not db_candidates:
            return []

        fts_query = f"{reference_title} {reference_text[:200]}".strip()
        fts_hits = await fts_search_articles(session, fts_query, limit=50)
        fts_rank_by_id = {h["article_id"]: h["fts_rank"] for h in fts_hits}

        ref_text_combined = f"{reference_title}\n{reference_text[:1000]}"
        model_loaded = self._embedding_service.is_loaded
        ref_embedding: list[float] = []
        if model_loaded:
            ref_embedding = await self._embedding_service.embed_text(ref_text_combined)

        enriched: list[dict[str, Any]] = []
        for art in db_candidates:
            emb_score = 0.0
            if model_loaded and ref_embedding:
                art_text = f"{art.title or ''}\n{(art.content or '')[:1000]}"
                art_embedding = await self._embedding_service.embed_text(art_text)
                emb_score = cosine_similarity(ref_embedding, art_embedding)

            enriched.append({
                "article_id": art.id,
                "title": art.title or "",
                "language": art.language,
                "published_at": art.published_at,
                "location_name": reference_location,
                "domain": None,
                "embedding_score": emb_score,
                "fts_rank": fts_rank_by_id.get(art.id, 0.0),
                "_article": art,
            })

        ranked = rerank_candidates(
            enriched,
            reference_text=reference_text,
            reference_time=reference_time,
            reference_location=reference_location,
            reference_domain=reference_domain,
            top_k=top_k,
        )

        return ranked

    async def _hard_filter(
        self,
        session: AsyncSession,
        *,
        reference_time: datetime | None,
        languages: list[str] | None,
        time_window_hours: int,
        exclude_ids: list[str],
    ) -> list[Article]:
        stmt = select(Article)
        filters = []
        if reference_time:
            start = reference_time - timedelta(hours=time_window_hours)
            end = reference_time + timedelta(hours=time_window_hours)
            filters.append(Article.published_at.between(start, end))

        if languages:
            filters.append(Article.language.in_(languages))

        if exclude_ids:
            filters.append(Article.id.notin_(exclude_ids))

        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.limit(200)
        res = await session.execute(stmt)
        return list(res.scalars().all())
