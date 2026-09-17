"""
Numerical parsing and drift detection helpers.
"""
from __future__ import annotations

import re
from typing import Any

# Regular expressions to extract numbers (integers, floats, percentage, ranges)
NUMERIC_PATTERN = re.compile(r"\b\d+(?:,\d+)*(?:\.\d+)?\b")


def extract_numbers_from_text(text: str) -> list[float]:
    """Extract all numerical values from a text string as floats."""
    if not text:
        return []
    matches = NUMERIC_PATTERN.findall(text)
    numbers: list[float] = []
    for match in matches:
        clean_num = match.replace(",", "")
        try:
            numbers.append(float(clean_num))
        except ValueError:
            continue
    return numbers


def check_numerical_drift(
    val1: float | str | None,
    val2: float | str | None,
    tolerance: float = 0.05
) -> dict[str, Any]:
    """
    Compare two numeric values to check for numerical drift.

    Returns dict indicating whether drift occurred, percent change, and direction.
    """
    if val1 is None or val2 is None:
        return {"has_drift": False, "reason": "One or both values are missing"}

    try:
        n1 = float(val1) if isinstance(val1, (int, str)) else val1
        n2 = float(val2) if isinstance(val2, (int, str)) else val2
    except (ValueError, TypeError):
        return {"has_drift": False, "reason": "Values cannot be parsed as floats"}

    if n1 == 0:
        has_drift = n2 != 0
        diff = n2
        pct_change = float("inf") if n2 != 0 else 0.0
    else:
        diff = n2 - n1
        pct_change = abs(diff) / abs(n1)
        has_drift = pct_change > tolerance

    direction = "EQUAL"
    if diff > 0:
        direction = "INCREASE"
    elif diff < 0:
        direction = "DECREASE"

    return {
        "has_drift": has_drift,
        "val1": n1,
        "val2": n2,
        "diff": diff,
        "pct_change": pct_change,
        "direction": direction,
    }
