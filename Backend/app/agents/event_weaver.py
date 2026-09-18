"""
Agent 3: Event Weaver.

Determines whether candidate articles belong to the same real-world event cluster.
Combines temporal windowing, entity matching, and semantic vector similarity.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel

from app.llm.client import GroqClient
from app.llm.prompts import EVENT_WEAVER_ALIGNMENT_PROMPT
from app.retrieval.semantic_retriever import SemanticRetriever
from app.utils.text import extract_named_entities


class AlignmentResponseSchema(BaseModel):
    is_same_event: bool
    confidence: float
    reasoning: str


class EventWeaverAgent:
    """Agent 3: Event-Aware Claim Retrieval and Clustering agent."""

    def __init__(
        self,
        llm_client: GroqClient | None = None,
        semantic_retriever: SemanticRetriever | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.semantic_retriever = semantic_retriever or SemanticRetriever()

    async def align_candidate_article(
        self,
        event_info: dict[str, Any],
        candidate_article: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate if candidate article belongs to event cluster.
        """
        # 1. Deterministic entity & title similarity check
        canonical_title = event_info.get("title", "")
        cand_title = candidate_article.get("title", "")

        entities1 = set(extract_named_entities(canonical_title))
        entities2 = set(extract_named_entities(cand_title))
        shared_entities = list(entities1.intersection(entities2))

        # 2. Vector semantic similarity
        semantic_match = False
        similarity_score = 0.0
        if canonical_title and cand_title:
            rankings = self.semantic_retriever.rank_candidates(
                query_text=canonical_title,
                candidates=[{"text": cand_title}],
                top_k=1,
            )
            if rankings:
                similarity_score = rankings[0][1]
                semantic_match = similarity_score >= 0.50

        # 3. LLM verification if available
        if self.llm_client and self.llm_client.api_key:
            user_prompt = EVENT_WEAVER_ALIGNMENT_PROMPT.format(
                event_title=canonical_title,
                event_summary=event_info.get("canonical_summary", ""),
                event_time=event_info.get("event_time", ""),
                event_location=event_info.get("location_name", ""),
                candidate_title=cand_title,
                candidate_language=candidate_article.get("language", "en"),
                candidate_published_at=candidate_article.get("published_at", ""),
                candidate_text=(candidate_article.get("content") or "")[:2000],
            )
            res = await self.llm_client.generate_structured(
                system_prompt="You are an expert event alignment reasoning system.",
                user_prompt=user_prompt,
                response_schema=AlignmentResponseSchema,
                prompt_version="event_weaver_v1",
            )
            return {
                "is_same_event": res.is_same_event,
                "confidence": res.confidence,
                "reasoning": res.reasoning,
                "shared_entities": shared_entities,
                "semantic_similarity": round(similarity_score, 4),
            }

        # Fallback deterministic decision logic
        is_same = len(shared_entities) > 0 or semantic_match or similarity_score > 0.40
        confidence = round(max(similarity_score, 0.70 if len(shared_entities) > 0 else 0.50), 2)

        return {
            "is_same_event": is_same,
            "confidence": confidence,
            "reasoning": f"Shared entities: {shared_entities}. Semantic similarity: {similarity_score:.2f}.",
            "shared_entities": shared_entities,
            "semantic_similarity": round(similarity_score, 4),
        }

    async def align_articles(
        self,
        event_id: str,
        articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Align candidate articles within an event cluster."""
        if not articles or len(articles) < 2:
            return []
        primary = articles[0]
        event_info = {"title": primary.get("title", ""), "id": event_id}
        results = []
        for cand in articles[1:]:
            res = await self.align_candidate_article(event_info, cand)
            results.append(res)
        return results

