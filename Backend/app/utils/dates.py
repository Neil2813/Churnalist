"""
Date/time parsing and normalization utilities.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dateutil_parser


def parse_date(raw: Any) -> datetime | None:
    """
    Attempt to parse a date value into a UTC-aware datetime.

    Accepts:
    - datetime objects (converted to UTC if naive)
    - ISO 8601 strings
    - RFC 2822 strings (common in RSS feeds)
    - feedparser's time.struct_time tuples
    - None (returns None)

    Returns None if parsing fails rather than raising.
    """
    if raw is None:
        return None

    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)

    # feedparser returns 9-tuples from time.struct_time
    if isinstance(raw, tuple) and len(raw) >= 6:
        try:
            import calendar
            ts = calendar.timegm(raw[:9])
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            pass

    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            dt = dateutil_parser.parse(raw, fuzzy=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    return None


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def format_iso(dt: datetime | None) -> str | None:
    """Format a datetime to ISO 8601 string with Z suffix, or None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
