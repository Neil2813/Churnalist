"""
Multi-signal candidate reranker.

Takes a list of candidates that have been through FTS and semantic retrieval,
attaches individual signal scores, then computes a weighted final score and
returns them sorted highest-first.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.analysis.entities import extract_entities
from app.retrieval.scoring import (
    compute_entity_overlap_score,
    compute_final_score,
    compute_location_score,
    compute_source_context_score,
    compute_temporal_score,
    normalise_fts_rank,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def rerank_candidates(
    candidates: list[dict[str, Any]],
    *,
    reference_text: str = "",
    reference_time: datetime | None = None,
    reference_location: str | None = None,
    reference_domain: str | None = None,
    weights: dict[str, float] | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    Rerank a list of candidate dicts by weighted multi-signal score.

    Expected candidate keys:
        - article_id / claim_id  (str)
        - title / raw_text       (str, used for entity extraction)
        - embedding_score        (float, 0–1, from semantic retrieval)
        - fts_rank               (float ≥ 0, raw BM25 rank from FTS5)
        - published_at           (datetime | None, for temporal scoring)
        - location_name          (str | None)
        - domain                 (str | None, publisher domain)

    Returns sorted list (best first) with 'final_score' and component scores attached.
    """
    if not candidates:
        return []

    # Extract reference entities for entity overlap scoring
    ref_entities: set[str] = set()
    if reference_text:
        ref_entities = {e.lower() for e in extract_entities(reference_text)}

    scored: list[dict[str, Any]] = []

    for cand in candidates:
        # --- Embedding score (already 0–1 from semantic retriever) ---
        embedding_score = float(cand.get("embedding_score", 0.0))

        # --- Lexical score (normalise FTS5 rank) ---
        fts_rank = float(cand.get("fts_rank", 0.0))
        lexical_score = normalise_fts_rank(fts_rank)

        # --- Entity overlap ---
        cand_text = cand.get("title", "") or cand.get("raw_text", "") or ""
        cand_entities = {e.lower() for e in extract_entities(cand_text)}
        entity_score = compute_entity_overlap_score(ref_entities, cand_entities)

        # --- Temporal proximity ---
        cand_time: datetime | None = cand.get("published_at")
        temporal_score = compute_temporal_score(cand_time, reference_time)

        # --- Location match ---
        location_score = compute_location_score(
            reference_location, cand.get("location_name")
        )

        # --- Source domain match ---
        source_score = compute_source_context_score(
            reference_domain, cand.get("domain")
        )

        final = compute_final_score(
            embedding_score=embedding_score,
            lexical_score=lexical_score,
            entity_score=entity_score,
            temporal_score=temporal_score,
            location_score=location_score,
            source_score=source_score,
            weights=weights,
        )

        scored.append({
            **cand,
            "embedding_score": embedding_score,
            "lexical_score": lexical_score,
            "entity_score": entity_score,
            "temporal_score": temporal_score,
            "location_score": location_score,
            "source_score": source_score,
            "final_score": final,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    logger.debug(
        "reranker_complete",
        total=len(scored),
        top_score=scored[0]["final_score"] if scored else 0,
    )
    return scored[:top_k]
