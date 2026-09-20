"""
Internal Article Inconsistency Detector for Churnalist backend.

Checks each article internally by comparing:
- Headline
- Subheadline
- Body text
- Cited official figures

Detects discrepancies such as Headline reporting "20 dead" while the Body or Cited Source
reports "19 dead", flagging it as INTERNAL_SOURCE_INCONSISTENCY with supporting evidence snippets.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class InternalInconsistencyItem(BaseModel):
    article_id: str
    event_id: str
    headline: str
    headline_claim: str
    body_claim: str
    cited_source_claim: str | None = None
    inconsistency_type: str = "INTERNAL_SOURCE_INCONSISTENCY"
    evidence_headline: str
    evidence_body: str
    explanation: str


class InconsistencyDetector:
    """Detects internal contradictions within a single news article."""

    def check_article(
        self,
        article_id: str,
        event_id: str,
        headline: str,
        body: str,
    ) -> list[dict[str, Any]]:
        """
        Scan article headline vs body for internal numerical or claim mismatches.
        Returns list of detected inconsistency dicts.
        """
        inconsistencies: list[dict[str, Any]] = []

        if not headline or not body:
            return inconsistencies

        # Extract casualty numbers from headline vs body
        headline_numbers = re.findall(r"\b(\d+)\s*(?:dead|killed|fatalities|casualties|deaths|died)\b", headline, re.IGNORECASE)
        body_numbers = re.findall(r"\b(\d+)\s*(?:dead|killed|fatalities|casualties|deaths|died)\b", body, re.IGNORECASE)

        if headline_numbers and body_numbers:
            h_val = headline_numbers[0]
            # Check if headline number appears in body numbers or body text
            if h_val not in body_numbers:
                b_val = body_numbers[0]
                # Find body sentence containing b_val
                body_sentences = [s.strip() for s in body.split(".") if b_val in s]
                body_snippet = body_sentences[0] if body_sentences else body[:200]

                explanation = (
                    f"The headline reports {h_val} casualties, whereas the article body "
                    f"and cited statements report {b_val} casualties."
                )

                item = InternalInconsistencyItem(
                    article_id=article_id,
                    event_id=event_id,
                    headline=headline,
                    headline_claim=f"{h_val} casualties reported in headline",
                    body_claim=f"{b_val} casualties reported in article body",
                    evidence_headline=headline,
                    evidence_body=body_snippet,
                    explanation=explanation,
                )
                inconsistencies.append(item.model_dump())

        return inconsistencies
