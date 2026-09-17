"""
Text processing utilities for DRIFT.

Covers:
- Text truncation for LLM context windows
- Sentence splitting
- Named-entity extraction helpers
- Numeric normalization across scripts
"""
from __future__ import annotations

import re
import unicodedata

# ── Numeric normalization ─────────────────────────────────────────────────────

# Devanagari (Hindi) digits
_DEVANAGARI = str.maketrans("०१२३४५६७८९", "0123456789")
# Tamil digits
_TAMIL = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")
# Telugu digits
_TELUGU = str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789")
# Bengali digits
_BENGALI = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
# Arabic-Indic digits
_ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

_ALL_DIGIT_MAPS = [_DEVANAGARI, _TAMIL, _TELUGU, _BENGALI, _ARABIC_INDIC]

# Written-out number words (English only — extend per language as needed)
_WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
    "lakh": 100_000, "million": 1_000_000,
}

# Approximate qualifiers
_APPROX_PATTERNS = re.compile(
    r"\b(around|about|approximately|roughly|nearly|over|more than|"
    r"at least|up to|almost|close to|~)\b",
    re.IGNORECASE,
)


def normalize_script_digits(text: str) -> str:
    """Convert non-ASCII digit scripts to ASCII digits."""
    for table in _ALL_DIGIT_MAPS:
        text = text.translate(table)
    return text


def extract_numbers(text: str) -> list[dict]:
    """
    Extract all numbers from text, including approximate qualifiers.

    Returns a list of dicts:
    {
        "raw": "around 20",
        "normalized_value": 20,
        "qualifier": "approximate" | None,
        "start": int,
        "end": int,
    }
    """
    text_normalized = normalize_script_digits(text)
    results = []

    # Find numeric literals (including commas as thousands separator, decimals)
    for m in re.finditer(r"\b\d[\d,]*(?:\.\d+)?\b", text_normalized):
        start, end = m.start(), m.end()
        raw_num = m.group().replace(",", "")
        try:
            value = float(raw_num) if "." in raw_num else int(raw_num)
        except ValueError:
            continue

        # Check for approximate qualifier in a 30-char window before the number
        window = text_normalized[max(0, start - 30): start]
        qualifier = "approximate" if _APPROX_PATTERNS.search(window) else None

        results.append({
            "raw": text_normalized[max(0, start - 8): end].strip(),
            "normalized_value": value,
            "qualifier": qualifier,
            "start": start,
            "end": end,
        })

    return results


# ── Text utilities ─────────────────────────────────────────────────────────────

def truncate_for_llm(text: str, max_chars: int = 8000) -> str:
    """
    Truncate article text for an LLM context window.

    Cuts at a paragraph boundary where possible rather than mid-sentence.
    """
    if len(text) <= max_chars:
        return text

    cut = text[:max_chars]
    # Try to cut at last paragraph boundary
    last_para = cut.rfind("\n\n")
    if last_para > max_chars * 0.5:
        return cut[:last_para].strip()
    # Fall back to last sentence boundary
    last_sent = max(cut.rfind(". "), cut.rfind(".\n"))
    if last_sent > max_chars * 0.5:
        return cut[:last_sent + 1].strip()
    return cut.strip()


def split_into_sentences(text: str) -> list[str]:
    """
    Rudimentary sentence splitter that preserves punctuation.

    For the hackathon this is deterministic and dependency-free.
    """
    # Split on . ? ! followed by whitespace + capital or end of string
    raw = re.split(r"(?<=[.?!])\s+(?=[A-Z\u0900-\u097F\u0B80-\u0BFF])", text)
    return [s.strip() for s in raw if s.strip()]


def clean_whitespace(text: str) -> str:
    """Normalize multiple spaces/tabs to single space, preserving newlines."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def word_count(text: str) -> int:
    """Rough word count — splits on whitespace."""
    return len(text.split())


def extract_named_entities(text: str) -> list[str]:
    """
    Extract candidate named entities from text.

    Delegates to app.analysis.entities for the core logic.
    Kept here as a re-export so legacy imports from app.utils.text continue
    to work without changes to the agents layer.
    """
    from app.analysis.entities import extract_entities
    return extract_entities(text)


def clean_text(text: str) -> str:
    """
    Alias for clean_whitespace for backward compatibility with agent imports.
    Normalizes multiple spaces/tabs to single space, preserving newlines.
    """
    return clean_whitespace(text)
