"""
Agent 4: Drift Investigator.

Flagship analysis agent evaluating claim transformations across language editions and articles:
- Module A: Churnalism Detection (Source Overlap)
- Module B: Multilingual Claim Drift Classification
- Module C: Correction Tracking
"""
from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel, Field

from app.analysis.numbers import check_numerical_drift
from app.analysis.source_overlap import analyze_source_overlap
from app.core.constants import RelationType, CorrectionType
from app.llm.client import GroqClient
from app.llm.prompts import DRIFT_INVESTIGATOR_PROMPT


class ClaimRelationItemSchema(BaseModel):
    source_claim_id: str
    target_claim_id: str
    relation_type: RelationType
    confidence: float = 1.0
    reason: str


class DriftAnalysisResponseSchema(BaseModel):
    relations: list[ClaimRelationItemSchema] = Field(default_factory=list)


class DriftInvestigatorAgent:
    """Agent 4: Information Drift & Churnalism Investigation Agent."""

    def __init__(self, llm_client: GroqClient | None = None) -> None:
        self.llm_client = llm_client

    def analyze_churnalism(self, source_content: str, target_content: str) -> dict[str, Any]:
        """Module A: Deterministic source overlap and churnalism score."""
        return analyze_source_overlap(source_content, target_content)

    async def investigate_claim_drift(
        self,
        source_claims: list[dict[str, Any]],
        target_claims: list[dict[str, Any]],
        source_lang: str = "en",
        target_lang: str = "en",
    ) -> list[dict[str, Any]]:
        """Module B: Multilingual claim drift comparison."""
        if self.llm_client and self.llm_client.api_key and source_claims and target_claims:
            user_prompt = DRIFT_INVESTIGATOR_PROMPT.format(
                source_lang=source_lang,
                source_claims_json=json.dumps(source_claims, default=str),
                target_lang=target_lang,
                target_claims_json=json.dumps(target_claims, default=str),
            )
            res = await self.llm_client.generate_structured(
                system_prompt="You are an expert factual drift investigation engine.",
                user_prompt=user_prompt,
                response_schema=DriftAnalysisResponseSchema,
                prompt_version="drift_investigator_v1",
            )
            return [rel.model_dump() for rel in res.relations]

        # Deterministic fallback comparison matching subject/predicate
        relations = []
        for s_claim in source_claims:
            s_subj = (s_claim.get("subject") or "").lower()
            s_pred = (s_claim.get("predicate") or "").lower()
            s_val = s_claim.get("object_value")

            for t_claim in target_claims:
                t_subj = (t_claim.get("subject") or "").lower()
                t_pred = (t_claim.get("predicate") or "").lower()
                t_val = t_claim.get("object_value")

                if s_subj == t_subj and s_pred == t_pred:
                    # Check numerical drift if both values are present
                    num_res = check_numerical_drift(s_val, t_val)
                    if num_res["has_drift"]:
                        rel_type = RelationType.NUMERICAL_DRIFT
                        reason = f"Numerical value drifted from {s_val} to {t_val}."
                    elif s_claim.get("attribution") and not t_claim.get("attribution"):
                        rel_type = RelationType.ATTRIBUTION_LOSS
                        reason = f"Attribution '{s_claim.get('attribution')}' was dropped."
                    elif s_val == t_val:
                        rel_type = RelationType.SAME
                        reason = "Claims match in value and meaning."
                    else:
                        rel_type = RelationType.MODIFIED
                        reason = f"Claim value modified from '{s_val}' to '{t_val}'."

                    relations.append({
                        "source_claim_id": s_claim.get("id", ""),
                        "target_claim_id": t_claim.get("id", ""),
                        "relation_type": rel_type,
                        "confidence": 0.90,
                        "reason": reason,
                    })

        return relations

    def track_corrections(
        self,
        event_id: str,
        articles: list[dict[str, Any]],
        claims: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Module C: Detect official corrections or retractions."""
        corrections = []
        # Check articles with correction titles/content
        for art in articles:
            content_lower = (art.get("content") or "").lower()
            if "correction:" in content_lower or "updated:" in content_lower:
                corrections.append({
                    "event_id": event_id,
                    "article_id": art.get("id"),
                    "correction_type": CorrectionType.FACTUAL_CORRECTION,
                    "original_text": "Prior casualty count / details",
                    "corrected_text": art.get("title", "Updated report"),
                    "correction_url": art.get("url"),
                    "detected_at": art.get("retrieved_at"),
                })
        return corrections
