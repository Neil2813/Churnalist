"""
Candidate Retriever for Churnalist event matching.

Calculates event-match scores using:
- 0.25 semantic similarity
- 0.20 location overlap
- 0.20 entity overlap
- 0.15 incident type similarity
- 0.10 temporal proximity
- 0.10 lexical/headline similarity

Casualty numbers are explicitly ignored during candidate event matching.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

from app.core.config import get_settings
from app.services.event_context_service import EventContext

settings = get_settings()


class CandidateRetriever:
    """Evaluates search result candidates against an EventContext."""

    def __init__(self) -> None:
        self.w_semantic = settings.match_weight_semantic
        self.w_location = settings.match_weight_location
        self.w_entities = settings.match_weight_entities
        self.w_incident = settings.match_weight_incident
        self.w_temporal = settings.match_weight_temporal
        self.w_headline = settings.match_weight_headline

    def score_candidate(
        self,
        candidate: dict[str, Any],
        context: EventContext,
    ) -> float:
        """
        Score a search result candidate against EventContext.
        Returns score in [0.0, 1.0].
        """
        title = candidate.get("title", "")
        snippet = candidate.get("snippet", "")
        cand_text = f"{title} {snippet}"
        cand_lower = cand_text.lower()

        # 1. Location Overlap (0.20)
        loc_score = 0.0
        if context.locations:
            matched = sum(1 for loc in context.locations if loc.lower() in cand_lower)
            loc_score = matched / len(context.locations)

        # 2. Entity Overlap (0.20)
        ent_score = 0.0
        all_ents = context.organizations + context.people + context.important_entities
        if all_ents:
            matched_ent = sum(1 for e in all_ents if e.lower() in cand_lower)
            ent_score = matched_ent / len(all_ents)

        # 3. Incident Type Similarity (0.15)
        inc_score = 0.0
        if context.incident_type and context.incident_type.lower() in cand_lower:
            inc_score = 1.0
        elif any(w.lower() in cand_lower for w in context.incident_title.split() if len(w) > 4):
            inc_score = 0.6

        # 4. Strict Temporal Proximity & Year Guardrail
        temp_score = 0.5
        if context.anchor_timestamp:
            anchor_year = context.anchor_timestamp.year
            # Check for conflicting 4-digit years in snippet/title
            found_years = [int(y) for y in re.findall(r"\b(20[0-9]{2})\b", cand_text)]
            if found_years and all(abs(y - anchor_year) > 1 for y in found_years):
                return 0.0  # Immediately reject candidates mentioning unrelated years (e.g. 2026 for 2020 anchor)

            cand_pub = candidate.get("published_at")
            if cand_pub:
                try:
                    if isinstance(cand_pub, str):
                        from app.utils.dates import parse_date
                        cand_dt = parse_date(cand_pub)
                    else:
                        cand_dt = cand_pub
                    if cand_dt:
                        days_diff = abs((cand_dt - context.anchor_timestamp).total_seconds()) / 86400.0
                        if days_diff > 30:
                            return 0.0  # Strictly reject candidates > 30 days away from anchor incident date
                        temp_score = float(math.exp(-((days_diff / 5.0) ** 2)))
                except Exception:
                    temp_score = 0.5

        # 5. Headline Lexical Similarity (0.10) (Stripping casualty digits)
        clean_title = re.sub(r"\b\d+\b", "", title).lower()
        clean_distinct = [w.lower() for w in context.distinctive_headline_terms]
        lex_score = 0.0
        if clean_distinct:
            matched_words = sum(1 for w in clean_distinct if w in clean_title)
            lex_score = matched_words / len(clean_distinct)

        # 6. Semantic Similarity (0.25)
        # Combination of lexical & text overlap without numbers
        sem_score = (loc_score * 0.4) + (ent_score * 0.4) + (inc_score * 0.2)

        final_score = (
            (self.w_semantic * sem_score)
            + (self.w_location * loc_score)
            + (self.w_entities * ent_score)
            + (self.w_incident * inc_score)
            + (self.w_temporal * temp_score)
            + (self.w_headline * lex_score)
        )

        return round(min(1.0, max(0.0, final_score)), 4)

    def filter_candidates(
        self,
        candidates: list[dict[str, Any]],
        context: EventContext,
        min_threshold: float = 0.20,
    ) -> list[dict[str, Any]]:
        """Score and filter candidates above minimum match threshold."""
        scored: list[dict[str, Any]] = []
        for cand in candidates:
            score = self.score_candidate(cand, context)
            if score >= min_threshold:
                cand_copy = dict(cand)
                cand_copy["match_score"] = score
                scored.append(cand_copy)

        scored.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
        return scored
