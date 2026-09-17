"""
Agent 5: Truth Trail.

Synthesizes structured drift evidence, extracted claims, provenance edges,
and correction records into a clear, evidence-first report.
"""
from __future__ import annotations

import json
from typing import Any

from app.llm.client import GroqClient
from app.llm.prompts import TRUTH_TRAIL_REPORT_PROMPT
from app.schemas.reports import ReportResponse, DriftHighlight, CorrectionHighlight


class TruthTrailAgent:
    """Agent 5: Report Synthesis Agent."""

    def __init__(self, llm_client: GroqClient | None = None) -> None:
        self.llm_client = llm_client

    async def generate_provenance_report(
        self,
        event_info: dict[str, Any],
        articles: list[dict[str, Any]],
        claims: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        corrections: list[dict[str, Any]],
    ) -> ReportResponse:
        """Generate human-readable evidence-backed report."""
        if self.llm_client and self.llm_client.api_key:
            articles_summary = json.dumps([
                {
                    "title": a.get("title"),
                    "language": a.get("language"),
                    "source_name": a.get("source_name") or a.get("source_id"),
                }
                for a in articles[:10]
            ])
            user_prompt = TRUTH_TRAIL_REPORT_PROMPT.format(
                event_title=event_info.get("title", "Event Provenance Report"),
                event_summary=event_info.get("canonical_summary", "No summary available"),
                articles_count=len(articles),
                articles_summary=articles_summary,
                drift_relations_summary=json.dumps(relations[:15], default=str),
                corrections_summary=json.dumps(corrections, default=str),
            )
            res = await self.llm_client.generate_structured(
                system_prompt="You are an evidence-first news provenance analysis agent.",
                user_prompt=user_prompt,
                response_schema=ReportResponse,
                prompt_version="truth_trail_v1",
            )
            res.event_id = event_info.get("id", "")
            return res

        # Deterministic fallback synthesis when LLM client is offline
        drifts: list[DriftHighlight] = []
        for rel in relations:
            r_type = rel.get("relation_type", "")
            if r_type in ("NUMERICAL_DRIFT", "ATTRIBUTION_LOSS", "MODIFIED", "SEVERITY_AMPLIFICATION"):
                drifts.append(
                    DriftHighlight(
                        category=r_type,
                        source_language="en",
                        target_language="ta",
                        original_text="Source report claim",
                        drifted_text="Edition modified claim",
                        explanation=rel.get("reason", "Claim value altered between editions."),
                        severity_level="MEDIUM",
                    )
                )

        corr_highlight = None
        if corrections:
            corr = corrections[0]
            corr_highlight = CorrectionHighlight(
                original_claim=corr.get("original_text", ""),
                corrected_claim=corr.get("corrected_text", ""),
                updated_articles_count=1,
                outdated_articles_count=max(0, len(articles) - 1),
                details="Official correction updated casualty/detail numbers.",
            )

        summary_text = (
            f"Analyzed {len(articles)} article editions for event '{event_info.get('title', 'News Event')}'. "
            f"Found {len(drifts)} key claim transformations across coverage."
        )

        return ReportResponse(
            id=f"rep_{event_info.get('id', 'demo')}",
            event_id=event_info.get("id", ""),
            headline=f"Provenance Analysis: {event_info.get('title', 'News Event')}",
            summary=summary_text,
            key_drifts=drifts,
            correction_status=corr_highlight,
            reader_takeaway="Cross-reference regional editions against official source releases to verify reported numbers.",
            confidence_score=0.90,
            evidence_sources=[{"title": a.get("title"), "url": a.get("url")} for a in articles[:5]],
            created_at=event_info.get("created_at") or "2026-09-17T20:00:00Z",
        )
