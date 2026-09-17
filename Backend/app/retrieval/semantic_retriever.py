"""
Semantic vector retrieval service for claim and document similarity.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

from app.core.constants import MIN_EMBEDDING_SIMILARITY
from app.embeddings.service import EmbeddingService


def cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


class SemanticRetriever:
    """Retriever computing semantic similarity matches over vector embeddings."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        if embedding_service is None:
            from app.core.config import get_settings
            s = get_settings()
            embedding_service = EmbeddingService(
                model_name=s.embedding_model,
                device=s.embedding_device,
            )
        self.embedding_service = embedding_service

    def rank_candidates(
        self,
        query_text: str,
        candidates: list[dict[str, Any]],
        top_k: int = 10,
        threshold: float = MIN_EMBEDDING_SIMILARITY,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Rank candidate items against query_text based on vector similarity.
        Candidates dict must contain either 'text' or precomputed 'embedding'.

        Note: this is a synchronous call intended for offline / batched use.
        For async embedding calls, use EmbeddingService.embed_many() directly.
        """
        if not query_text or not candidates:
            return []

        # If model not loaded, return empty (graceful degradation)
        if not self.embedding_service.is_loaded:
            return []

        import asyncio
        loop = asyncio.new_event_loop()
        try:
            all_texts = [query_text] + [
                item.get("text", item.get("raw_text", "")) for item in candidates
            ]
            all_texts = [t or "" for t in all_texts]
            vectors = loop.run_until_complete(self.embedding_service.embed_many(all_texts))
        finally:
            loop.close()

        query_vector = vectors[0]
        scored: list[tuple[dict[str, Any], float]] = []

        for i, item in enumerate(candidates):
            item_vector = item.get("embedding") or vectors[i + 1]
            if item_vector:
                score = cosine_similarity(query_vector, item_vector)
                if score >= threshold:
                    scored.append((item, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
