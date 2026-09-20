"""
Event Context derivation and Search Query Generation service.

Extracts event identity (locations, incident type, entities, date) from an anchor
article, explicitly excluding casualty numbers from primary event identity.
Generates multi-pass search queries across a +/- 10 day window.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.llm.client import GroqClient

logger = get_logger(__name__)


@dataclass
class EventContext:
    incident_title: str
    incident_type: str
    locations: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    event_date: str | None = None
    anchor_timestamp: datetime | None = None
    search_window_start: datetime | None = None
    search_window_end: datetime | None = None
    important_entities: list[str] = field(default_factory=list)
    distinctive_headline_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.anchor_timestamp:
            d["anchor_timestamp"] = self.anchor_timestamp.isoformat()
        if self.search_window_start:
            d["search_window_start"] = self.search_window_start.isoformat()
        if self.search_window_end:
            d["search_window_end"] = self.search_window_end.isoformat()
        return d


class EventContextService:
    """Service to extract EventContext from anchor article and generate search queries."""

    def __init__(self, groq_client: GroqClient | None = None) -> None:
        self.groq_client = groq_client or GroqClient()

    def sanitize_headline_terms(self, title: str) -> list[str]:
        """Strip numbers and common noise words to keep distinctive terms."""
        # Strip digits/casualty numbers
        no_digits = re.sub(r"\b\d+\b", "", title)
        words = re.findall(r"\b[A-Za-z]{3,}\b", no_digits)
        stop = {"kills", "dead", "killed", "die", "died", "after", "with", "from", "that", "this", "were", "been", "have", "news", "report"}
        return [w for w in words if w.lower() not in stop]

    async def build_event_context(
        self,
        title: str,
        content: str,
        published_at: datetime | None = None,
        source_name: str | None = None,
    ) -> EventContext:
        """Derive event context using LLM reasoning + deterministic cleanup."""
        now = datetime.now(timezone.utc)
        anchor_ts = published_at or now
        win_start = anchor_ts - timedelta(days=10)
        win_end = anchor_ts + timedelta(days=10)

        # Default fallback context derived deterministically
        distinctive_terms = self.sanitize_headline_terms(title or "")
        incident_title = title or "News Event"

        context = EventContext(
            incident_title=incident_title,
            incident_type="news event",
            locations=[],
            countries=[],
            people=[],
            organizations=[],
            event_date=anchor_ts.strftime("%Y-%m-%d"),
            anchor_timestamp=anchor_ts,
            search_window_start=win_start,
            search_window_end=win_end,
            important_entities=[],
            distinctive_headline_terms=distinctive_terms,
        )

        # Try Groq for structured entity & incident extraction if content is available
        if title or content:
            prompt = f"""You are a news intelligence analyst. Analyze the following news article anchor and extract the core real-world event identity.

IMPORTANT RULE:
DO NOT include casualty numbers, death tolls, injured counts, or numerical values in the event identity or incident type. Casualty figures change over time and across reports.

Anchor Title: {title}
Anchor Text: {content[:2000]}

Respond ONLY with valid JSON matching this exact structure:
{{
  "incident_title": "Short descriptive title of event without numbers",
  "incident_type": "e.g. bus crash, earthquake, election, train derailment, fire",
  "locations": ["City", "District", "State"],
  "countries": ["Country"],
  "people": ["Name"],
  "organizations": ["Org/Company"],
  "event_date": "YYYY-MM-DD",
  "important_entities": ["Key entity names"]
}}"""
            try:
                raw_res = await self.groq_client.generate_json(
                    prompt=prompt,
                    system_prompt="Extract structured event context without casualty numbers. Return strict JSON.",
                    temperature=0.1,
                )
                if isinstance(raw_res, dict):
                    context.incident_title = raw_res.get("incident_title") or context.incident_title
                    context.incident_type = raw_res.get("incident_type") or context.incident_type
                    context.locations = raw_res.get("locations") or []
                    context.countries = raw_res.get("countries") or []
                    context.people = raw_res.get("people") or []
                    context.organizations = raw_res.get("organizations") or []
                    context.important_entities = raw_res.get("important_entities") or []
                    if raw_res.get("event_date"):
                        context.event_date = raw_res["event_date"]
            except Exception as exc:
                logger.warning("event_context_groq_extraction_failed", error=str(exc))

        return context

    def generate_search_queries(self, context: EventContext) -> list[str]:
        """
        Generate multiple search queries around:
        1. headline concepts (sans numbers)
        2. location + incident type
        3. important entities
        4. event date / month
        5. source names

        Casualty numbers are NEVER required.
        """
        queries: list[str] = []
        loc_str = " ".join(context.locations[:2])
        org_str = " ".join(context.organizations[:2])
        inc_type = context.incident_type if context.incident_type != "news event" else ""

        # 1. Primary location + incident type + orgs
        if loc_str or inc_type or org_str:
            q1 = f"{org_str} {inc_type} {loc_str}".strip()
            if q1:
                queries.append(q1)

        # 2. Location + incident type
        if loc_str and inc_type:
            queries.append(f"{loc_str} {inc_type}")

        # 3. Distinctive headline terms
        if context.distinctive_headline_terms:
            queries.append(" ".join(context.distinctive_headline_terms[:5]))

        # 4. Location + Entities + Date
        date_str = ""
        if context.event_date:
            try:
                dt = datetime.strptime(context.event_date[:10], "%Y-%m-%d")
                date_str = dt.strftime("%B %Y")
            except Exception:
                date_str = context.event_date[:7]

        if loc_str and date_str:
            queries.append(f"{loc_str} {inc_type} {date_str}".strip())

        # 5. Organizations + Location + Date
        if org_str and loc_str:
            queries.append(f"{org_str} {loc_str} {date_str}".strip())

        # Fallback to incident title if no queries generated
        if not queries:
            queries.append(context.incident_title)

        # Extract year string to restrict searches to the anchor event year
        year_str = ""
        if context.anchor_timestamp:
            year_str = str(context.anchor_timestamp.year)
        elif context.event_date:
            year_str = context.event_date[:4]

        # Ensure uniqueness while preserving order and appending year_str
        unique_queries: list[str] = []
        for q in queries:
            clean_q = re.sub(r"\s+", " ", q).strip()
            if year_str and year_str not in clean_q:
                clean_q = f"{clean_q} {year_str}".strip()
            if clean_q and clean_q not in unique_queries:
                unique_queries.append(clean_q)

        return unique_queries[:6]
