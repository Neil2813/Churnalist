"""
Semantic drift calculation utilities.

Provides structured drift metrics for cross-language and cross-edition
claim comparison. Deliberately separates deterministic signal computation
from LLM-based semantic labelling.

Drift types tracked:
    NUMBER_CHANGE           — numeric value changed
    ADDITION                — claim present in target but not source
    OMISSION                — claim present in source but not target
    ATTRIBUTION_LOSS        — source attribution stripped
    SEVERITY_AMPLIFICATION  — severity wording escalated
    SEVERITY_SOFTENING      — severity wording de-escalated
    CERTAINTY_CHANGE        — certainty modifier changed
    CONTRADICTION           — mutually exclusive claims
"""
from __future__ import annotations

import re
from typing import Any

from app.analysis.numbers import check_numerical_drift
from app.core.constants import RelationType


# ── Severity vocabulary (ordered low → high) ──────────────────────────────────

SEVERITY_LEVELS: dict[str, int] = {
    "unharmed": 0,
    "uninjured": 0,
    "minor": 1,
    "slightly injured": 1,
    "injured": 2,
    "seriously injured": 3,
    "critically injured": 4,
    "feared dead": 5,
    "reportedly dead": 5,
    "dead": 6,
    "killed": 6,
    "confirmed dead": 7,
}

# Certainty modifier vocabulary
CERTAINTY_MODIFIERS: frozenset[str] = frozenset({
    "confirmed", "verified", "proven",
    "reported", "allegedly", "reportedly", "claimed",
    "feared", "suspected", "unconfirmed",
    "according to", "officials said", "police said",
})


def detect_severity_change(
    source_text: str,
    target_text: str,
) -> dict[str, Any]:
    """
    Detect severity amplification or softening between two claim texts.

    Returns:
        {
            "has_change": bool,
            "direction": "AMPLIFICATION" | "SOFTENING" | "NONE",
            "source_level": str | None,
            "target_level": str | None,
            "source_score": int,
            "target_score": int,
        }
    """
    src_lower = source_text.lower()
    tgt_lower = target_text.lower()

    src_match = _best_severity_match(src_lower)
    tgt_match = _best_severity_match(tgt_lower)

    src_score = SEVERITY_LEVELS.get(src_match, -1) if src_match else -1
    tgt_score = SEVERITY_LEVELS.get(tgt_match, -1) if tgt_match else -1

    if src_score == -1 or tgt_score == -1 or src_score == tgt_score:
        return {
            "has_change": False,
            "direction": "NONE",
            "source_level": src_match,
            "target_level": tgt_match,
            "source_score": src_score,
            "target_score": tgt_score,
        }

    direction = "AMPLIFICATION" if tgt_score > src_score else "SOFTENING"
    return {
        "has_change": True,
        "direction": direction,
        "source_level": src_match,
        "target_level": tgt_match,
        "source_score": src_score,
        "target_score": tgt_score,
    }


def detect_certainty_change(
    source_text: str,
    target_text: str,
) -> dict[str, Any]:
    """
    Detect changes in certainty / epistemic modality between two claim texts.
    """
    src_mods = _extract_certainty_modifiers(source_text.lower())
    tgt_mods = _extract_certainty_modifiers(target_text.lower())

    added = tgt_mods - src_mods
    removed = src_mods - tgt_mods

    return {
        "has_change": bool(added or removed),
        "source_modifiers": sorted(src_mods),
        "target_modifiers": sorted(tgt_mods),
        "added_modifiers": sorted(added),
        "removed_modifiers": sorted(removed),
    }


def detect_attribution_loss(
    source_text: str,
    target_text: str,
) -> bool:
    """
    Return True if the source had explicit attribution that the target omits.

    Simple heuristic: checks for 'said', 'according to', 'confirmed' patterns.
    """
    attribution_patterns = [
        r"\bsaid\b",
        r"\baccording to\b",
        r"\bconfirmed\b",
        r"\bannounced\b",
        r"\bstated\b",
    ]
    src_has = any(re.search(p, source_text.lower()) for p in attribution_patterns)
    tgt_has = any(re.search(p, target_text.lower()) for p in attribution_patterns)

    return src_has and not tgt_has


def classify_claim_relation(
    source_claim: dict[str, Any],
    target_claim: dict[str, Any],
    embedding_similarity: float = 0.0,
) -> dict[str, Any]:
    """
    Classify the drift relation between two aligned claim dicts.

    Expected claim dict keys: raw_text, object_value, object_unit,
    severity, certainty, attribution.

    Returns:
        {
            "relation_type": RelationType,
            "confidence": float,
            "reason": str,
            "evidence": dict,
        }
    """
    src_text = source_claim.get("raw_text", "") or ""
    tgt_text = target_claim.get("raw_text", "") or ""

    evidence: dict[str, Any] = {}

    # ── Numeric drift ─────────────────────────────────────────────────────────
    src_val = source_claim.get("object_value")
    tgt_val = target_claim.get("object_value")
    if src_val and tgt_val:
        num_result = check_numerical_drift(src_val, tgt_val)
        if num_result.get("has_drift"):
            evidence["numeric"] = num_result
            return {
                "relation_type": RelationType.NUMERICAL_DRIFT,
                "confidence": 0.90,
                "reason": f"Numeric value changed from {src_val} to {tgt_val}.",
                "evidence": evidence,
            }

    # ── Severity change ───────────────────────────────────────────────────────
    sev_result = detect_severity_change(src_text, tgt_text)
    if sev_result["has_change"]:
        evidence["severity"] = sev_result
        rel = (
            RelationType.SEVERITY_AMPLIFICATION
            if sev_result["direction"] == "AMPLIFICATION"
            else RelationType.SEVERITY_SOFTENING
        )
        return {
            "relation_type": rel,
            "confidence": 0.85,
            "reason": f"Severity {sev_result['direction'].lower()}: "
                      f"'{sev_result['source_level']}' → '{sev_result['target_level']}'.",
            "evidence": evidence,
        }

    # ── Attribution loss ──────────────────────────────────────────────────────
    if detect_attribution_loss(src_text, tgt_text):
        evidence["attribution_loss"] = True
        return {
            "relation_type": RelationType.ATTRIBUTION_LOSS,
            "confidence": 0.80,
            "reason": "Source attribution dropped in the target claim.",
            "evidence": evidence,
        }

    # ── Certainty change ──────────────────────────────────────────────────────
    cert_result = detect_certainty_change(src_text, tgt_text)
    if cert_result["has_change"]:
        evidence["certainty"] = cert_result
        return {
            "relation_type": RelationType.CERTAINTY_CHANGE,
            "confidence": 0.75,
            "reason": "Certainty modifier changed between source and target claim.",
            "evidence": evidence,
        }

    # ── High similarity → SAME ────────────────────────────────────────────────
    if embedding_similarity >= 0.90:
        return {
            "relation_type": RelationType.SAME,
            "confidence": embedding_similarity,
            "reason": "Claims are semantically equivalent.",
            "evidence": {},
        }

    # ── Moderate similarity → MODIFIED ───────────────────────────────────────
    if embedding_similarity >= 0.60:
        return {
            "relation_type": RelationType.MODIFIED,
            "confidence": embedding_similarity,
            "reason": "Claims are related but semantically modified.",
            "evidence": {},
        }

    # ── Low similarity → potentially CONTRADICTS ──────────────────────────────
    return {
        "relation_type": RelationType.CONTRADICTS,
        "confidence": 0.60,
        "reason": "Claims appear to describe the same subject with differing content.",
        "evidence": {},
    }


def compute_drift_summary(
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate drift statistics across a list of claim relations.

    Relations must each have a 'relation_type' key.
    """
    totals: dict[str, int] = {}
    for rel in relations:
        rt = str(rel.get("relation_type", "UNKNOWN"))
        totals[rt] = totals.get(rt, 0) + 1

    drifting_types = {
        RelationType.NUMERICAL_DRIFT,
        RelationType.SEVERITY_AMPLIFICATION,
        RelationType.SEVERITY_SOFTENING,
        RelationType.CERTAINTY_CHANGE,
        RelationType.ATTRIBUTION_LOSS,
        RelationType.CONTRADICTS,
        RelationType.MODIFIED,
    }

    drifting_count = sum(
        count for rt, count in totals.items() if rt in {str(t) for t in drifting_types}
    )

    return {
        "total_relations": len(relations),
        "drifting_count": drifting_count,
        "categories_breakdown": totals,
        "numerical_drifts": totals.get(RelationType.NUMERICAL_DRIFT, 0),
        "severity_changes": totals.get(RelationType.SEVERITY_AMPLIFICATION, 0) + totals.get(RelationType.SEVERITY_SOFTENING, 0),
        "attribution_losses": totals.get(RelationType.ATTRIBUTION_LOSS, 0),
        "certainty_changes": totals.get(RelationType.CERTAINTY_CHANGE, 0),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _best_severity_match(text: str) -> str | None:
    """Find the highest-priority severity phrase present in text."""
    found: list[tuple[str, int]] = []
    for phrase, level in SEVERITY_LEVELS.items():
        if phrase in text:
            found.append((phrase, level))
    if not found:
        return None
    # Return the most specific (longest) match at the highest level
    found.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
    return found[0][0]


def _extract_certainty_modifiers(text: str) -> set[str]:
    """Return certainty modifiers present in text."""
    return {mod for mod in CERTAINTY_MODIFIERS if mod in text}
