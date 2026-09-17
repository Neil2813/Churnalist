"""
Event-aware candidate article retriever.

Combines FTS5 lexical search + semantic embedding similarity +
hard metadata filters to surface candidate articles that may belong
to the same real-world event as a reference article.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EVENT_CLUSTER_WINDOW_HOURS, MAX_SEMANTIC_CANDIDATES
from app.core.logging import get_logger
from app.db.models.article import Article
from app.retrieval.fts_retriever import fts_search_articles
from app.retrieval.reranker import rerank_candidates
from app.retrieval.semantic_retriever import SemanticRetriever, cosine_similarity
from app.embeddings.service import EmbeddingService

logger = get_logger(__name__)


class EventRetriever:
    """
    Retrieves candidate articles likely to describe the same real-world event.

    Execution order:
        1. Hard filter  — date window + language filter (from DB)
        2. FTS          — keyword-level lexical hits (from FTS5 index)
        3. Semantic     — embedding cosine similarity (in-process)
        4. Rerank       — merge + multi-signal score sort
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        if embedding_service is None:
            from app.core.config import get_settings
            s = get_settings()
            embedding_service = EmbeddingService(
                model_name=s.embedding_model,
                device=s.embedding_device,
            )
        self._embedding_service = embedding_service
        self._semantic_retriever = SemanticRetriever(self._embedding_service)

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
        """
        Return top-k candidate articles likely belonging to the same event.

        Each returned dict includes the Article fields plus signal scores.
        """
        # ── Step 1: Hard DB filter ────────────────────────────────────────────
        db_candidates = await self._hard_filter(
            session,
            reference_time=reference_time,
            languages=languages,
            time_window_hours=time_window_hours,
            exclude_ids=exclude_article_ids or [],
        )

        if not db_candidates:
            return []

        # ── Step 2: FTS5 lexical search ───────────────────────────────────────
        fts_query = f"{reference_title} {reference_text[:200]}".strip()
        fts_hits = await fts_search_articles(session, fts_query, limit=50)
        fts_rank_by_id = {h["article_id"]: h["fts_rank"] for h in fts_hits}

        # ── Step 3: Semantic embedding similarity ─────────────────────────────
        ref_text_combined = f"{reference_title}\n{reference_text[:1000]}"

        # Graceful degradation: skip semantic scoring if model not loaded
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
                "location_name": reference_location,  # use reference for now
                "domain": None,
                "embedding_score": emb_score,
                "fts_rank": fts_rank_by_id.get(art.id, 0.0),
                # Attach original ORM object for downstream use
                "_article": art,
            })

        # ── Step 4: Multi-signal rerank ───────────────────────────────────────
        ranked = rerank_candidates(
            enriched,
            reference_text=reference_text,
            reference_time=reference_time,
            reference_location=reference_location,
            reference_domain=reference_domain,
            top_k=top_k,
        )

        logger.info(
            "event_retriever_complete",
            db_candidates=len(db_candidates),
            fts_hits=len(fts_hits),
            ranked=len(ranked),
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
        """Return articles passing hard metadata filters."""
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

        stmt = stmt.limit(200)  # cap DB scan
        res = await session.execute(stmt)
        return list(res.scalars().all())
