"""
Language analysis utilities.

Wraps langdetect for primary language detection and provides helpers for:
  - language classification and confidence assessment
  - cross-language article pair labelling (translated vs. rewritten)
  - language metadata normalisation
"""
from __future__ import annotations

from app.core.constants import LANGUAGE_NAMES, SUPPORTED_LANGUAGES
from app.core.logging import get_logger
from app.ingestion.normalizer import ArticleNormalizer

logger = get_logger(__name__)


def detect_language(
    text: str,
    default_lang: str | None = None,
) -> tuple[str | None, float | None]:
    """
    Detect ISO 639-1 language code and confidence for a text snippet.

    Delegates to ArticleNormalizer.detect_language which uses langdetect
    with seed=0 for deterministic output.
    """
    return ArticleNormalizer.detect_language(text, default_lang=default_lang)


def is_supported_language(lang_code: str | None) -> bool:
    """Return True if the language is in the DRIFT supported languages set."""
    if not lang_code:
        return False
    return lang_code.lower() in SUPPORTED_LANGUAGES


def get_language_name(lang_code: str | None) -> str:
    """Return human-readable language name for a given ISO code."""
    if not lang_code:
        return "Unknown"
    return LANGUAGE_NAMES.get(lang_code.lower(), lang_code.upper())


def classify_article_pair_relation(
    source_lang: str | None,
    target_lang: str | None,
    content_overlap: float,
) -> str:
    """
    Classify the relationship between two articles based on language and overlap.

    Returns one of:
        TRANSLATED     — different languages, high semantic overlap
        REWRITTEN      — same language, moderate overlap (churnalism risk)
        ORIGINAL       — same language, low overlap (independent coverage)
        LOCALIZED      — same language family, moderate overlap
        UNKNOWN
    """
    if not source_lang or not target_lang:
        return "UNKNOWN"

    same_lang = source_lang.lower() == target_lang.lower()

    if not same_lang and content_overlap >= 0.50:
        return "TRANSLATED"
    elif same_lang and content_overlap >= 0.40:
        return "REWRITTEN"
    elif same_lang and content_overlap < 0.20:
        return "ORIGINAL"
    elif not same_lang:
        return "LOCALIZED"

    return "UNKNOWN"


def detect_correction_language_signal(text: str, lang: str | None = None) -> bool:
    """
    Return True if the text contains language-level correction signals.

    Checks English keywords plus common signals in Hindi/Tamil/Bengali.
    """
    if not text:
        return False

    text_lower = text.lower()

    # English signals
    english_signals = [
        "correction", "corrected", "editor's note", "editors note",
        "retraction", "retracted", "updated", "update:", "clarification",
        "revised", "amendment",
    ]
    if any(sig in text_lower for sig in english_signals):
        return True

    # Hindi Unicode signals (सुधार = correction, संशोधन = amendment)
    hindi_signals = ["सुधार", "संशोधन", "अपडेट"]
    if (lang == "hi" or lang is None) and any(sig in text for sig in hindi_signals):
        return True

    # Tamil Unicode signals (திருத்தம் = correction, புதுப்பிப்பு = update, புதுப்பிக்கப்பட்டது = updated, விளக்கம் = clarification)
    tamil_signals = ["திருத்தம்", "புதுப்பிப்பு", "புதுப்பிக்கப்பட்டது", "விளக்கம்", "பிழைதிருத்தம்"]
    if (lang == "ta" or lang is None) and any(sig in text for sig in tamil_signals):
        return True

    # Telugu Unicode signals (సవరణ = correction/amendment, నవీకరణ = update, నవీకరించబడింది = updated, స్పష్టీకరణ = clarification)
    telugu_signals = ["సవరణ", "నవీకరణ", "నవీకరించబడింది", "స్పష్టీకరణ", "దిద్దుబాటు"]
    if (lang == "te" or lang is None) and any(sig in text for sig in telugu_signals):
        return True

    # Bengali Unicode signals (সংশোধন = correction/amendment, আপডেট = update, সংশোধিত = corrected, স্পষ্টীকরণ = clarification)
    bengali_signals = ["সংশোধন", "আপডেট", "সংশোধিত", "স্পষ্টীকরণ", "ভুল সংশোধন"]
    if (lang == "bn" or lang is None) and any(sig in text for sig in bengali_signals):
        return True

    # Kannada Unicode signals (ತಿದ್ದುಪಡಿ = correction/amendment, ಸರಿಪಡಿಸಲಾಗಿದೆ = corrected, ನವೀಕರಣ = update, ನವೀಕರಿಸಲಾಗಿದೆ = updated, ಸ್ಪಷ್ಟೀಕರಣ = clarification, ತಿದ್ದುಪಡಿ ಮಾಡಲಾಗಿದೆ = corrected, ಅಪ್‌ಡೇಟ್ = update)
    kannada_signals = ["ತಿದ್ದುಪಡಿ", "ಸರಿಪಡಿಸಲಾಗಿದೆ", "ನವೀಕರಣ", "ನವೀಕರಿಸಲಾಗಿದೆ", "ಸ್ಪಷ್ಟೀಕರಣ", "ತಿದ್ದುಪಡಿ ಮಾಡಲಾಗಿದೆ", "ಅಪ್‌ಡೇಟ್"]
    if (lang == "kn" or lang is None) and any(sig in text for sig in kannada_signals):
        return True

    return False


def get_language_pair_label(lang1: str | None, lang2: str | None) -> str:
    """Return a readable label for a cross-language pair, e.g. 'en→hi'."""
    l1 = (lang1 or "?").lower()
    l2 = (lang2 or "?").lower()
    return f"{l1}→{l2}"
