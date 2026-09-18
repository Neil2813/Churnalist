"""
PipelineContext — shared state container for a single analysis pipeline run.

Agents receive a PipelineContext rather than direct DB sessions or
arbitrary application state. This creates an explicit data contract
and makes agent testing straightforward (inject a mock context).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PipelineContext:
    """
    Immutable identity + mutable working state for one analysis pipeline execution.

    Agents should update the list fields as they produce results, but must NOT
    persist those results directly to the database — that is the pipeline's job.
    """

    # ── Identity (set at pipeline start, never mutated) ───────────────────────
    run_id: str
    event_id: str
    pipeline_version: str = "1.0"

    # ── Seed input ────────────────────────────────────────────────────────────
    seed_url: str | None = None
    seed_languages: list[str] = field(default_factory=lambda: ["en"])

    # ── Working state (populated by agents in sequence) ───────────────────────
    article_ids: list[str] = field(default_factory=list)
    claim_ids: list[str] = field(default_factory=list)
    relation_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)

    # ── Intermediate results (kept in memory, not persisted individually) ─────
    # Raw claim dicts from ClaimMiner before DB persistence
    raw_claims: list[dict[str, Any]] = field(default_factory=list)
    # Aligned claim group dicts from EventWeaver
    aligned_claim_groups: list[dict[str, Any]] = field(default_factory=list)
    # Drift relation dicts from DriftInvestigator
    raw_relations: list[dict[str, Any]] = field(default_factory=list)
    # Correction dicts from DriftInvestigator correction pass
    raw_corrections: list[dict[str, Any]] = field(default_factory=list)
    # Final report dict from TruthTrail
    report: dict[str, Any] = field(default_factory=dict)

    # ── Progress tracking ─────────────────────────────────────────────────────
    # Set by ProgressTracker; agents should not write these directly
    current_stage: str = "QUEUED"
    progress_pct: int = 0

    # ── Metrics accumulator ───────────────────────────────────────────────────
    metrics: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error: str | None = None

    # ── Candidate retrieval results ───────────────────────────────────────────
    candidate_article_ids: list[str] = field(default_factory=list)

    def add_metric(self, key: str, value: Any) -> None:
        """Accumulate a named metric value."""
        self.metrics[key] = value

    def elapsed_seconds(self) -> float:
        """Return seconds elapsed since pipeline start."""
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a lightweight summary dict for logging and status responses."""
        return {
            "run_id": self.run_id,
            "event_id": self.event_id,
            "pipeline_version": self.pipeline_version,
            "current_stage": self.current_stage,
            "progress_pct": self.progress_pct,
            "articles": len(self.article_ids),
            "claims": len(self.claim_ids),
            "relations": len(self.relation_ids),
            "corrections": len(self.correction_ids),
            "elapsed_seconds": round(self.elapsed_seconds(), 2),
            "error": self.error,
        }
