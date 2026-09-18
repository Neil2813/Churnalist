"""Async web article fetcher and extractor enforcing network security and size limits."""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, ValidationError
from app.core.logging import get_logger
from app.ingestion.html_cleaner import HTMLCleaner

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class ExtractedArticle:
    """Parsed and extracted news article payload."""
    url: str
    canonical_url: str | None
    title: str | None
    text: str
    author: str | None
    published_date_str: str | None
    raw_html: str
    status_code: int
    metadata: dict[str, Any]


@dataclass
class RawArticle:
    """Standardized payload emitted by news providers."""
    url: str
    canonical_url: str | None = None
    url_hash: str | None = None
    title: str | None = None
    content: str | None = None
    content_hash: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    extraction_status: str = "FULL"
    source_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


async def fetch_and_extract(url: str, http_client: httpx.AsyncClient | None = None) -> RawArticle:
    """Fetch and extract a URL into a RawArticle."""
    extractor = ArticleExtractor()
    extracted = await extractor.extract_from_url(url)
    from app.utils.dates import parse_date
    from app.utils.hashing import content_hash
    from app.utils.urls import normalize_url, url_to_hash

    canon = extracted.canonical_url or normalize_url(url)
    pub = parse_date(extracted.published_date_str)
    return RawArticle(
        url=url,
        canonical_url=canon,
        url_hash=url_to_hash(canon),
        title=extracted.title,
        content=extracted.text,
        content_hash=content_hash(extracted.text) if extracted.text else None,
        published_at=pub,
        retrieved_at=datetime.now(timezone.utc),
        extraction_status="FULL" if extracted.text else "PARTIAL",
        metadata=extracted.metadata,
    )


class AsyncWebFetcher:
    """
    Asynchronous web fetcher enforcing security controls:
    - HTTP/HTTPS schemes only
    - Private / Loopback IP address blocking (SSRF prevention)
    - Max response size cap (`MAX_ARTICLE_BYTES`)
    - Configurable timeouts
    """

    PRIVATE_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fe80::/10"),
    ]

    def __init__(self, timeout: float | None = None, max_bytes: int | None = None):
        self.timeout = timeout or float(settings.request_timeout_seconds)
        self.max_bytes = max_bytes or settings.max_article_bytes

    def validate_url(self, url: str) -> None:
        """Validate scheme and resolve host to ensure target is not a private IP."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise ValidationError("Invalid URL: missing hostname.")

        # Check for direct localhost/private hostname
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            raise ValidationError(f"Access to local hostname '{hostname}' is forbidden.")

        # DNS resolution check for private IP ranges
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)
                for private_net in self.PRIVATE_NETWORKS:
                    if ip_obj in private_net:
                        raise ValidationError(f"Access to private IP address '{ip_str}' is forbidden.")
        except socket.gaierror as err:
            logger.warning("dns_resolution_failed", hostname=hostname, error=str(err))

    async def fetch(self, url: str) -> tuple[str, int]:
        """Fetch raw HTML string for a URL safely."""
        self.validate_url(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DRIFT-Bot/1.0 NewsProvenance/Research",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, max_redirects=5) as client:
            try:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code >= 400:
                        raise ExternalServiceError(
                            f"HTTP {response.status_code} error fetching URL {url}.",
                            status_code=response.status_code
                        )

                    content_bytes = bytearray()
                    async for chunk in response.aiter_bytes():
                        content_bytes.extend(chunk)
                        if len(content_bytes) > self.max_bytes:
                            raise ValidationError(
                                f"Response size exceeds maximum permitted threshold of {self.max_bytes} bytes."
                            )

                    raw_html = content_bytes.decode("utf-8", errors="replace")
                    return raw_html, response.status_code

            except httpx.TimeoutException as exc:
                raise ExternalServiceError(f"Timeout fetching URL {url}: {exc}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"HTTP fetch error for URL {url}: {exc}") from exc


class ArticleExtractor:
    """High-level extractor combining AsyncWebFetcher and HTMLCleaner."""

    def __init__(self, fetcher: AsyncWebFetcher | None = None, cleaner: HTMLCleaner | None = None):
        self.fetcher = fetcher or AsyncWebFetcher()
        self.cleaner = cleaner or HTMLCleaner()

    async def extract_from_url(self, url: str) -> ExtractedArticle:
        """Fetch and extract structured article content from direct URL."""
        raw_html, status_code = await self.fetcher.fetch(url)
        cleaned = self.cleaner.extract(raw_html, fallback_url=url)

        return ExtractedArticle(
            url=url,
            canonical_url=cleaned.canonical_url,
            title=cleaned.title,
            text=cleaned.text,
            author=cleaned.author,
            published_date_str=cleaned.published_date_str,
            raw_html=raw_html,
            status_code=status_code,
            metadata=cleaned.metadata
        )

    def extract_from_html(self, raw_html: str, url: str) -> ExtractedArticle:
        """Extract structured article content directly from a raw HTML string."""
        cleaned = self.cleaner.extract(raw_html, fallback_url=url)
        return ExtractedArticle(
            url=url,
            canonical_url=cleaned.canonical_url,
            title=cleaned.title,
            text=cleaned.text,
            author=cleaned.author,
            published_date_str=cleaned.published_date_str,
            raw_html=raw_html,
            status_code=200,
            metadata=cleaned.metadata
        )
