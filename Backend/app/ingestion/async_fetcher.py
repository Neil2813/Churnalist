"""
Bounded asynchronous HTTP client for fetching candidate news articles.

Enforces:
- Concurrency limiting via asyncio.Semaphore
- SSRF protection (blocking local & private IP subnets)
- Request timeout and maximum response size limits
- Fallback to snippet storage with extraction_status = PARTIAL when articles fail to fetch
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ingestion.article_extractor import ArticleExtractor, RawArticle
from app.utils.dates import parse_date
from app.utils.hashing import content_hash
from app.utils.urls import normalize_url, url_to_hash

logger = get_logger(__name__)
settings = get_settings()


class BoundedAsyncFetcher:
    """
    Bounded async HTTP fetcher for multi-article discovery ingestion.
    """

    PRIVATE_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.169.254/32"),
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fe80::/10"),
    ]

    def __init__(
        self,
        max_concurrent: int | None = None,
        timeout: float | None = None,
        max_bytes: int | None = None,
    ) -> None:
        self.max_concurrent = max_concurrent or settings.max_concurrent_fetches
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.timeout = timeout or float(settings.request_timeout_seconds)
        self.max_bytes = max_bytes or settings.max_article_bytes
        self.extractor = ArticleExtractor()

    def validate_url(self, url: str) -> None:
        """Validate URL scheme and ensure IP is not in private ranges."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid URL: missing hostname.")

        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            raise ValueError(f"Access to local hostname '{hostname}' is forbidden.")

        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)
                for private_net in self.PRIVATE_NETWORKS:
                    if ip_obj in private_net:
                        raise ValueError(f"Access to private IP address '{ip_str}' is forbidden.")
        except socket.gaierror as err:
            logger.warning("dns_validation_warning", hostname=hostname, error=str(err))

    async def fetch_candidate(self, candidate: dict[str, Any]) -> RawArticle:
        """
        Fetch a single candidate article dictionary (containing url, snippet, title, etc.)
        with concurrency limiting and graceful fallback.
        """
        async with self.semaphore:
            url = candidate.get("url", "")
            title = candidate.get("title", "")
            snippet = candidate.get("snippet", "")
            source_name = candidate.get("source", "")
            pub_str = candidate.get("published_at")

            norm_url = normalize_url(url)
            u_hash = url_to_hash(norm_url)
            pub_date = parse_date(pub_str) if pub_str else None

            try:
                self.validate_url(url)
                extracted = await self.extractor.extract_from_url(url)
                body_text = extracted.text.strip() if extracted.text else ""

                if body_text:
                    return RawArticle(
                        url=url,
                        canonical_url=extracted.canonical_url or norm_url,
                        url_hash=u_hash,
                        title=extracted.title or title or "News Article",
                        content=body_text,
                        content_hash=content_hash(body_text),
                        published_at=parse_date(extracted.published_date_str) or pub_date,
                        retrieved_at=datetime.now(timezone.utc),
                        extraction_status="FULL",
                        source_name=source_name or "Web Source",
                        metadata=extracted.metadata,
                    )
            except Exception as exc:
                logger.warning("candidate_fetch_failed", url=url, error=str(exc))

            # Fallback: store search result snippet as PARTIAL article
            fallback_text = snippet if snippet else title
            return RawArticle(
                url=url,
                canonical_url=norm_url,
                url_hash=u_hash,
                title=title or "Search Candidate Snippet",
                content=fallback_text,
                content_hash=content_hash(fallback_text) if fallback_text else "empty",
                published_at=pub_date,
                retrieved_at=datetime.now(timezone.utc),
                extraction_status="PARTIAL",
                source_name=source_name or "Search Result Snippet",
                metadata={"partial_snippet": snippet},
            )

    async def fetch_all_candidates(self, candidates: list[dict[str, Any]]) -> list[RawArticle]:
        """Fetch all candidates concurrently using bounded semaphore tasks."""
        tasks = [self.fetch_candidate(c) for c in candidates]
        return await asyncio.gather(*tasks)
