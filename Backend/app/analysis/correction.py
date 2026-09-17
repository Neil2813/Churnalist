"""
Deterministic correction detection and analysis.

Corrections are detected using a layered strategy:
    Layer 1 — Keyword signal scan (fastest, most reliable)
    Layer 2 — Numeric claim comparison across article versions
    Layer 3 — Surviving article tracking (which indexed articles still
               carry the old claim)

Intent is never inferred. The system states:
    "11 indexed articles still contain the earlier claim."
Not:
    "11 articles deliberately misrepresent the facts."
"""
from __future__ import annotations

import re
from typing import Any

from app.core.constants import CORRECTION_KEYWORDS, CorrectionType
from app.analysis.language import detect_correction_language_signal
from app.analysis.numbers import check_numerical_drift, extract_numbers_from_text


# ── Layer 1: Keyword-based detection ─────────────────────────────────────────

def detect_correction_keywords(text: str, lang: str | None = None) -> bool:
    """Return True if text contains known correction/retraction language."""
    if not text:
        return False

    text_lower = text.lower()
    if any(kw in text_lower for kw in CORRECTION_KEYWORDS):
        return True

    # Use language-sensitive signals as fallback
    return detect_correction_language_signal(text, lang=lang)


def extract_correction_context(text: str, window_chars: int = 300) -> list[str]:
    """
    Find sentences containing correction keywords and return surrounding context.

    Returns a list of text snippets (one per match site).
    """
    if not text:
        return []

    snippets: list[str] = []
    text_lower = text.lower()

    for kw in CORRECTION_KEYWORDS:
        start = 0
        while True:
            idx = text_lower.find(kw, start)
            if idx == -1:
                break
            snippet_start = max(0, idx - window_chars // 2)
            snippet_end = min(len(text), idx + len(kw) + window_chars // 2)
            snippets.append(text[snippet_start:snippet_end].strip())
            start = idx + 1

    return snippets


# ── Layer 2: Numeric claim change detection ───────────────────────────────────

def compare_numeric_claims(
    original_text: str,
    updated_text: str,
    tolerance: float = 0.05,
) -> dict[str, Any]:
    """
    Compare numbers between original and updated article text.

    Returns:
        {
            "has_numeric_change": bool,
            "original_numbers": list[float],
            "updated_numbers": list[float],
            "changed_values": list[dict],  # each: {original, updated, pct_change}
        }
    """
    orig_nums = extract_numbers_from_text(original_text)
    upd_nums = extract_numbers_from_text(updated_text)

    changed_values: list[dict[str, Any]] = []

    # Compare shortest list against longest; track paired positions
    min_len = min(len(orig_nums), len(upd_nums))
    for i in range(min_len):
        result = check_numerical_drift(orig_nums[i], upd_nums[i], tolerance=tolerance)
        if result.get("has_drift"):
            changed_values.append({
                "original": orig_nums[i],
                "updated": upd_nums[i],
                "pct_change": result.get("pct_change", 0.0),
                "direction": result.get("direction", "UNKNOWN"),
            })

    return {
        "has_numeric_change": len(changed_values) > 0,
        "original_numbers": orig_nums,
        "updated_numbers": upd_nums,
        "changed_values": changed_values,
    }


# ── Layer 3: Surviving article tracking ──────────────────────────────────────

def find_surviving_articles(
    original_claim_text: str,
    articles: list[dict[str, Any]],
    similarity_threshold: float = 0.70,
) -> list[str]:
    """
    Find indexed articles that still contain text similar to the original (now-corrected) claim.

    This uses simple token overlap rather than semantic similarity to keep this
    layer deterministic and fast.

    articles: list of {'id': str, 'content': str}

    Returns list of article IDs that still carry the original claim text.
    """
    if not original_claim_text or not articles:
        return []

    orig_tokens = set(re.findall(r"\b\w+\b", original_claim_text.lower()))
    surviving_ids: list[str] = []

    for art in articles:
        content = art.get("content", "") or ""
        art_tokens = set(re.findall(r"\b\w+\b", content.lower()))

        if not art_tokens:
            continue

        # Token containment: what fraction of the original claim's tokens appear in the article
        containment = len(orig_tokens & art_tokens) / len(orig_tokens) if orig_tokens else 0.0
        if containment >= similarity_threshold:
            surviving_ids.append(art["id"])

    return surviving_ids


# ── Correction classification ─────────────────────────────────────────────────

def classify_correction_type(
    original_text: str | None,
    corrected_text: str | None,
) -> CorrectionType:
    """
    Heuristically classify a correction based on what changed between claim texts.
    """
    if not original_text or not corrected_text:
        return CorrectionType.OTHER

    orig_lower = original_text.lower()
    corr_lower = corrected_text.lower()

    # Numeric change
    orig_nums = set(extract_numbers_from_text(orig_lower))
    corr_nums = set(extract_numbers_from_text(corr_lower))
    if orig_nums != corr_nums:
        return CorrectionType.NUMBER_CHANGE

    # Retraction pattern
    retraction_words = ["retract", "retraction", "withdrawn", "withdraw"]
    if any(w in corr_lower for w in retraction_words):
        return CorrectionType.RETRACTION

    # Date change
    date_patterns = [r"\b\d{4}\b", r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b"]
    for pat in date_patterns:
        orig_dates = re.findall(pat, orig_lower)
        corr_dates = re.findall(pat, corr_lower)
        if orig_dates != corr_dates:
            return CorrectionType.DATE_CHANGE

    # Clarification
    if "clarif" in corr_lower:
        return CorrectionType.CLARIFICATION

    return CorrectionType.FACTUAL_CORRECTION


# ── Main correction analysis entry point ──────────────────────────────────────

def analyze_article_for_corrections(
    article_content: str,
    article_lang: str | None = None,
    previous_content: str | None = None,
) -> dict[str, Any]:
    """
    Run all three correction detection layers on a single article.

    Returns:
        {
            "has_keyword_signal": bool,
            "correction_snippets": list[str],
            "has_numeric_change": bool,
            "numeric_changes": list[dict],
        }
    """
    result: dict[str, Any] = {
        "has_keyword_signal": False,
        "correction_snippets": [],
        "has_numeric_change": False,
        "numeric_changes": [],
    }

    # Layer 1
    result["has_keyword_signal"] = detect_correction_keywords(article_content, lang=article_lang)
    if result["has_keyword_signal"]:
        result["correction_snippets"] = extract_correction_context(article_content)

    # Layer 2
    if previous_content:
        numeric_result = compare_numeric_claims(previous_content, article_content)
        result["has_numeric_change"] = numeric_result["has_numeric_change"]
        result["numeric_changes"] = numeric_result["changed_values"]

    return result
