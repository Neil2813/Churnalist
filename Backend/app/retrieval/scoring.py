"""
Multi-signal retrieval scoring for candidate article/claim ranking.

Scoring formula (weights configurable via Settings):
    final_score =
        weight_embedding   * embedding_score
      + weight_lexical     * lexical_score
      + weight_entity      * entity_score
      + weight_temporal    * temporal_score
      + weight_location    * location_score
      + weight_source      * source_score

All individual signals must be normalised to [0.0, 1.0].
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.core.config import get_settings


def compute_temporal_score(
    candidate_time: datetime | None,
    reference_time: datetime | None,
    window_hours: int = 72,
) -> float:
    """
    Score temporal proximity on a Gaussian decay curve.

    Returns 1.0 for exact match, decaying toward 0.0 as gap grows
    beyond window_hours.
    """
    if candidate_time is None or reference_time is None:
        return 0.5  # neutral if unknown

    gap_hours = abs((candidate_time - reference_time).total_seconds()) / 3600.0
    # Gaussian decay: score = e^(-(gap/sigma)^2)
    sigma = window_hours / 2.0
    return float(math.exp(-((gap_hours / sigma) ** 2)))


def compute_entity_overlap_score(
    source_entities: set[str],
    target_entities: set[str],
) -> float:
    """
    Jaccard similarity over named-entity sets.
    Both sets should be lowercase-normalised before calling.
    """
    if not source_entities or not target_entities:
        return 0.0
    intersection = len(source_entities & target_entities)
    union = len(source_entities | target_entities)
    return intersection / union if union > 0 else 0.0


def compute_location_score(
    source_location: str | None,
    target_location: str | None,
) -> float:
    """
    Simple location match score.
    1.0 — same location string (case-insensitive)
    0.5 — one location contains the other
    0.0 — no match or missing
    """
    if not source_location or not target_location:
        return 0.0
    sl = source_location.lower().strip()
    tl = target_location.lower().strip()
    if sl == tl:
        return 1.0
    if sl in tl or tl in sl:
        return 0.5
    return 0.0


def compute_source_context_score(
    source_domain: str | None,
    candidate_domain: str | None,
) -> float:
    """Score based on publisher domain match (same outlet = 1.0, else 0.0)."""
    if not source_domain or not candidate_domain:
        return 0.0
    return 1.0 if source_domain.lower() == candidate_domain.lower() else 0.0


def normalise_fts_rank(rank: float, max_rank: float = 50.0) -> float:
    """Normalise FTS5 BM25 rank (lower = better) to [0, 1] (higher = better)."""
    if rank <= 0:
        return 0.0
    return min(1.0, rank / max_rank)


def compute_final_score(
    *,
    embedding_score: float = 0.0,
    lexical_score: float = 0.0,
    entity_score: float = 0.0,
    temporal_score: float = 0.0,
    location_score: float = 0.0,
    source_score: float = 0.0,
    weights: dict[str, float] | None = None,
) -> float:
    """
    Compute the weighted multi-signal final relevance score.

    All inputs must be in [0.0, 1.0]. Weights are read from Settings unless
    overridden, allowing per-request tuning in future.
    """
    if weights is None:
        weights = get_settings().scoring_weights

    score = (
        weights.get("embedding", 0.30) * embedding_score
        + weights.get("lexical", 0.20) * lexical_score
        + weights.get("entity", 0.20) * entity_score
        + weights.get("temporal", 0.15) * temporal_score
        + weights.get("location", 0.10) * location_score
        + weights.get("source", 0.05) * source_score
    )
    return round(min(1.0, max(0.0, score)), 6)


def score_candidate(
    candidate: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
) -> float:
    """
    Compute final score for a candidate dict that already has individual signal scores.

    Expected keys (all optional, default 0.0):
        embedding_score, lexical_score, entity_score,
        temporal_score, location_score, source_score
    """
    return compute_final_score(
        embedding_score=candidate.get("embedding_score", 0.0),
        lexical_score=candidate.get("lexical_score", 0.0),
        entity_score=candidate.get("entity_score", 0.0),
        temporal_score=candidate.get("temporal_score", 0.0),
        location_score=candidate.get("location_score", 0.0),
        source_score=candidate.get("source_score", 0.0),
        weights=weights,
    )
