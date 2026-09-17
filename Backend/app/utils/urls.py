"""
Utility functions for URL normalization and SSRF prevention.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, urljoin

from app.core.constants import TRACKING_PARAMS
from app.core.exceptions import InvalidURLError, SSRFBlockedError, UnsupportedURLSchemeError

# Private/reserved IP ranges to block for SSRF prevention
_BLOCKED_HOSTS = frozenset({
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",
})

_PRIVATE_IP_PATTERNS = re.compile(
    r"^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.|0\.0\.0\.0)"
)


def validate_url(url: str) -> str:
    """
    Validate a user-supplied URL for safety.

    - Must be http or https
    - Must not point to private/loopback addresses (SSRF prevention)
    - Must have a valid hostname

    Returns the cleaned URL or raises a domain exception.
    """
    if not url or not isinstance(url, str):
        raise InvalidURLError("URL must be a non-empty string")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise UnsupportedURLSchemeError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted.",
            details={"url": url},
        )

    host = (parsed.hostname or "").lower()
    if not host:
        raise InvalidURLError("URL has no hostname", details={"url": url})

    if host in _BLOCKED_HOSTS or _PRIVATE_IP_PATTERNS.match(host):
        raise SSRFBlockedError(
            "URL points to a private or loopback address and cannot be fetched.",
            details={"host": host},
        )

    return url


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication.

    - Lowercase scheme and host
    - Remove known tracking query parameters
    - Remove trailing slash from path (unless path is /)
    - Sort remaining query parameters for consistency
    """
    url = url.strip()
    parsed = urlparse(url)

    # Lowercase scheme + host
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip tracking params from query string
    qs = parse_qs(parsed.query, keep_blank_values=False)
    clean_qs = {k: v for k, v in qs.items() if k.lower() not in TRACKING_PARAMS}
    # Sort for consistency
    new_query = urlencode(sorted(clean_qs.items()), doseq=True)

    # Normalise path — remove trailing slash unless it's the root
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    normalised = urlunparse((scheme, netloc, path, parsed.params, new_query, ""))
    return normalised


def url_to_hash(url: str) -> str:
    """Return SHA-256 hex digest of a normalized URL."""
    normalised = normalize_url(url)
    return hashlib.sha256(normalised.encode()).hexdigest()


def extract_domain(url: str) -> str:
    """Return the bare domain (without www.) from a URL."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host.removeprefix("www.")
