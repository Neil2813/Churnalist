"""
Agent 2: Claim Miner.

Extracts atomic factual claims from news articles, preserves source spans,
and normalizes claim fields into structured domain models.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.core.constants import ClaimType
from app.llm.client import GroqClient
from app.llm.prompts import CLAIM_MINER_PROMPT, MULTILINGUAL_CLAIM_MINER_PROMPT


class ExtractedClaimSchema(BaseModel):
    """Schema for individual claim output from LLM."""
    claim_type: ClaimType = ClaimType.FACT
    subject: str
    predicate: str
    object_value: str
    object_unit: str | None = None
    attribution: str | None = None
    certainty: str | None = None
    severity: str | None = None
    raw_text: str
    original_language: str | None = None
    original_text: str | None = None
    english_translation: str | None = None
    extracted_value: str | None = None


class ClaimMinerOutputSchema(BaseModel):
    """LLM response container schema for extracted claims."""
    claims: list[ExtractedClaimSchema] = Field(default_factory=list)


class ClaimMinerAgent:
    """Agent 2: Atomic Claim Extraction agent."""

    def __init__(self, llm_client: GroqClient | None = None) -> None:
        self.llm_client = llm_client

    def find_source_span(self, article_content: str, raw_text: str) -> tuple[int | None, int | None]:
        """Find start and end character offsets of raw_text within full article content."""
        if not article_content or not raw_text:
            return None, None
        idx = article_content.find(raw_text)
        if idx != -1:
            return idx, idx + len(raw_text)
        # Try case-insensitive fallback search
        idx_lower = article_content.lower().find(raw_text.lower())
        if idx_lower != -1:
            return idx_lower, idx_lower + len(raw_text)
        return None, None

    async def mine_claims(
        self,
        article_id: str,
        event_id: str,
        title: str,
        content: str,
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """
        Extract claims from article text using LLM or deterministic fallback if LLM client is missing/unconfigured.
        For non-English articles, extracts factual claims and translates to English in a single call.
        """
        extracted_items: list[ExtractedClaimSchema] = []
        is_non_english = bool(language and language.lower() not in {"en", "eng"})

        if self.llm_client and self.llm_client.api_key:
            if is_non_english:
                user_prompt = MULTILINGUAL_CLAIM_MINER_PROMPT.format(
                    title=title,
                    language=language,
                    content=content[:8000],
                )
                result = await self.llm_client.generate_structured(
                    system_prompt="You are an expert factual claim extraction and multilingual translation system.",
                    user_prompt=user_prompt,
                    response_schema=ClaimMinerOutputSchema,
                    prompt_version="multilingual_claim_miner_v1",
                )
            else:
                user_prompt = CLAIM_MINER_PROMPT.format(
                    title=title,
                    language=language,
                    content=content[:8000],  # Bound input size
                )
                result = await self.llm_client.generate_structured(
                    system_prompt="You are an expert factual claim extraction system.",
                    user_prompt=user_prompt,
                    response_schema=ClaimMinerOutputSchema,
                    prompt_version="claim_miner_v1",
                )
            extracted_items = result.claims
        else:
            # Deterministic fallback claim extraction for demo / offline mode
            sentences = [s.strip() for s in content.split(".") if s.strip()]
            for sentence in sentences[:5]:
                extracted_items.append(
                    ExtractedClaimSchema(
                        claim_type=ClaimType.FACT,
                        subject="article",
                        predicate="states",
                        object_value=sentence[:100],
                        raw_text=sentence,
                        original_language=language,
                        original_text=sentence,
                        english_translation=sentence,
                        extracted_value=sentence[:100],
                    )
                )

        claims_out = []
        for claim in extracted_items:
            orig_text = claim.original_text or claim.raw_text
            span_text = orig_text or claim.raw_text
            start_offset, end_offset = self.find_source_span(content, span_text)

            orig_lang = claim.original_language or language
            eng_trans = claim.english_translation or (claim.raw_text if not is_non_english else orig_text)
            ext_val = claim.extracted_value or claim.object_value

            claims_out.append({
                "article_id": article_id,
                "event_id": event_id,
                "claim_type": claim.claim_type,
                "subject": claim.subject,
                "predicate": claim.predicate,
                "object_value": claim.object_value,
                "object_unit": claim.object_unit,
                "attribution": claim.attribution,
                "certainty": claim.certainty,
                "severity": claim.severity,
                "raw_text": claim.raw_text,
                "original_language": orig_lang,
                "original_text": orig_text,
                "english_translation": eng_trans,
                "extracted_value": ext_val,
                "source_start_offset": start_offset,
                "source_end_offset": end_offset,
            })

        return claims_out
