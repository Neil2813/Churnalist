"""
Content hashing utilities for deduplication.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata


def sha256_hex(text: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text_for_hashing(text: str) -> str:
    """
    Normalize text before hashing to improve deduplication across minor
    formatting differences (extra whitespace, BOM, Unicode variants).

    Does NOT strip punctuation — numbers and attribution markers matter.
    """
    # NFC Unicode normalization
    text = unicodedata.normalize("NFC", text)
    # Remove byte-order mark
    text = text.replace("\ufeff", "")
    # Collapse multiple whitespace into single space (preserve newlines as \n)
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple newlines into double newline (paragraph boundary)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    """
    Return a SHA-256 hash of normalised article content.

    This is used for duplicate detection and embedding cache keys.
    """
    normalised = normalize_text_for_hashing(text)
    return sha256_hex(normalised)


hash_content = content_hash


def hash_url(url: str) -> str:
    """Return SHA-256 hex digest of a URL string."""
    return sha256_hex(url.strip())


def embedding_cache_key(text: str, model_name: str) -> str:
    """
    Return a cache key for a text embedding.

    Format: SHA-256(normalized_text || "||" || model_name)
    """
    normalised = normalize_text_for_hashing(text)
    raw = f"{normalised}||{model_name}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

