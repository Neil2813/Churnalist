"""
Deterministic source overlap and churnalism analysis.

Computes Jaccard word overlap, n-gram containment, and numeric overlap.
"""
from __future__ import annotations

import re
from typing import Any

from app.analysis.numbers import extract_numbers_from_text


def _tokenize(text: str) -> set[str]:
    """Basic word tokenization stripping punctuation and converting to lowercase."""
    if not text:
        return set()
    words = re.findall(r"\b\w+\b", text.lower())
    return set(words)


def _get_ngrams(tokens: list[str], n: int = 3) -> set[tuple[str, ...]]:
    """Return n-grams as a set of tuples."""
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity coefficient between two texts."""
    set1 = _tokenize(text1)
    set2 = _tokenize(text2)
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0


def calculate_ngram_containment(source_text: str, target_text: str, n: int = 3) -> float:
    """
    Calculate what fraction of target's n-grams appear in the source text.
    Measures verbatim reproduction (churnalism).
    """
    source_words = re.findall(r"\b\w+\b", source_text.lower())
    target_words = re.findall(r"\b\w+\b", target_text.lower())

    source_ngrams = _get_ngrams(source_words, n=n)
    target_ngrams = _get_ngrams(target_words, n=n)

    if not target_ngrams:
        return 0.0

    shared = len(target_ngrams.intersection(source_ngrams))
    return shared / len(target_ngrams)


def analyze_source_overlap(source_content: str, target_content: str) -> dict[str, Any]:
    """
    Perform full deterministic overlap analysis between source and target documents.
    """
    jaccard = calculate_jaccard_similarity(source_content, target_content)
    trigram_containment = calculate_ngram_containment(source_content, target_content, n=3)

    source_nums = set(extract_numbers_from_text(source_content))
    target_nums = set(extract_numbers_from_text(target_content))

    numeric_overlap = 0.0
    if target_nums:
        numeric_overlap = len(source_nums.intersection(target_nums)) / len(target_nums)

    overall_overlap = (0.4 * jaccard) + (0.4 * trigram_containment) + (0.2 * numeric_overlap)

    assessment = "LOW_DEPENDENCE"
    if overall_overlap > 0.60:
        assessment = "HIGH_SOURCE_DEPENDENCE"
    elif overall_overlap > 0.35:
        assessment = "MODERATE_SOURCE_DEPENDENCE"

    return {
        "jaccard_similarity": round(jaccard, 4),
        "trigram_containment": round(trigram_containment, 4),
        "numeric_overlap": round(numeric_overlap, 4),
        "overall_overlap": round(overall_overlap, 4),
        "assessment": assessment,
    }
