"""
Named entity extraction and overlap scoring.

Uses a lightweight regex-based approach that works across languages
without requiring heavy NLP model loading at import time.

For production, replace with spaCy multilingual or a Groq-assisted
entity pass; the interface is identical.
"""
from __future__ import annotations

import re
from typing import Any


# ── Lightweight English-biased entity patterns ────────────────────────────────
# These capture the most common drift-relevant entity categories.

_CAPITALIZED_WORD = re.compile(r"\b[A-Z][a-z]{2,}\b")

# Common number words for multilingual numeric normalization
_NUMBER_WORDS: dict[str, float] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "thousand": 1000,
}

# Stopwords to filter from capitalized-word entity candidates
_STOPWORDS: frozenset[str] = frozenset({
    "The", "A", "An", "In", "On", "At", "By", "For", "Of", "To", "Is",
    "Was", "Are", "Were", "Has", "Had", "Have", "Been", "Be", "But", "And",
    "Or", "Not", "With", "That", "This", "They", "He", "She", "We", "It",
    "According", "Said", "Says", "Told", "After", "Before", "During", "While",
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
})


def extract_entities(text: str) -> list[str]:
    """
    Extract candidate named entities from text.

    Returns a deduplicated list of entity strings.
    For now uses capitalization heuristics; can be swapped for spaCy/Groq.
    """
    if not text:
        return []

    candidates = _CAPITALIZED_WORD.findall(text)
    entities: list[str] = []
    seen: set[str] = set()

    for word in candidates:
        if word in _STOPWORDS:
            continue
        if word not in seen:
            seen.add(word)
            entities.append(word)

    return entities


def extract_entity_set(text: str) -> set[str]:
    """Return deduplicated lowercase entity set for overlap calculations."""
    return {e.lower() for e in extract_entities(text)}


def compute_entity_overlap(
    source_text: str,
    target_text: str,
) -> dict[str, Any]:
    """
    Compute entity overlap between two texts.

    Returns:
        {
            "source_entities": [...],
            "target_entities": [...],
            "shared_entities": [...],
            "jaccard": float,
            "new_entities": [...],
            "dropped_entities": [...],
        }
    """
    src_entities = extract_entity_set(source_text)
    tgt_entities = extract_entity_set(target_text)

    shared = src_entities & tgt_entities
    new_in_target = tgt_entities - src_entities
    dropped_from_source = src_entities - tgt_entities

    union = src_entities | tgt_entities
    jaccard = len(shared) / len(union) if union else 0.0

    return {
        "source_entities": sorted(src_entities),
        "target_entities": sorted(tgt_entities),
        "shared_entities": sorted(shared),
        "new_entities": sorted(new_in_target),
        "dropped_entities": sorted(dropped_from_source),
        "jaccard": round(jaccard, 4),
        "shared_count": len(shared),
        "new_count": len(new_in_target),
        "dropped_count": len(dropped_from_source),
    }


def find_attribution_entities(text: str) -> list[str]:
    """
    Identify attribution phrases (who is cited as a source).

    Looks for patterns like 'X said', 'according to X', 'X confirmed'.
    """
    if not text:
        return []

    patterns = [
        r"(?:according to|per)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|confirmed|stated|told|announced|reported)",
        r"(?:officials?|police|authorities|government)\s+(?:said|confirmed|stated|announced)",
    ]

    found: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        found.extend(m for m in matches if isinstance(m, str) and m)

    return list(set(found))
