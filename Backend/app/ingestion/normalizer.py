"""Normalization utilities for URLs, text content, dates, and language detection."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any

from dateutil import parser as date_parser
from langdetect import DetectorFactory, detect_langs


from app.core.logging import get_logger
from app.utils.urls import normalize_url

logger = get_logger(__name__)

# Enforce deterministic results from langdetect
DetectorFactory.seed = 0


class ArticleNormalizer:
    """Normalizes raw extracted text, dates, URLs, and detects article language."""

    @staticmethod
    def normalize_article_url(url: str) -> str:
        """Canonicalize and strip tracking parameters from a URL."""
        return normalize_url(url)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean whitespace, zero-width characters, and normalize unicode."""
        if not text:
            return ""

        # Unicode NFC normalization
        normalized = unicodedata.normalize("NFC", text)
        # Remove zero-width spaces and control characters
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) not in ("Cf", "Cc") or ch in ("\n", "\t"))
        # Clean inline duplicate spaces while preserving paragraph breaks
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]
        cleaned_lines = [line for line in lines if line]
        return "\n\n".join(cleaned_lines)

    @staticmethod
    def parse_published_date(date_str: str | None) -> datetime | None:
        """Parse raw date string into datetime object."""
        if not date_str or not date_str.strip():
            return None

        try:
            parsed = date_parser.parse(date_str)
            return parsed
        except (ValueError, TypeError, OverflowError) as exc:
            logger.warning("date_parsing_failed", date_str=date_str, error=str(exc))
            return None

    @staticmethod
    def detect_language(text: str, default_lang: str | None = None) -> tuple[str | None, float | None]:
        """
        Detect ISO 639-1 language code and confidence score from article body text.
        """
        if not text or len(text.strip()) < 20:
            return default_lang, (1.0 if default_lang else None)

        try:
            predictions = detect_langs(text)
            if predictions:
                top = predictions[0]
                return top.lang, float(top.prob)
        except Exception as exc:
            logger.warning("language_detection_failed", error=str(exc))

        return default_lang, (1.0 if default_lang else None)


def normalize_article_text(text: str) -> str:
    """Module-level helper to normalize text."""
    return ArticleNormalizer.normalize_text(text)
