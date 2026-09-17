"""Unit tests for app.utils.urls module."""
import pytest
from app.utils.urls import validate_url, normalize_url, extract_domain, url_to_hash
from app.core.exceptions import InvalidURLError, SSRFBlockedError, UnsupportedURLSchemeError


def test_validate_url_valid():
    url = "https://news.example.com/article/123"
    assert validate_url(url) == url


def test_validate_url_unsupported_scheme():
    with pytest.raises(UnsupportedURLSchemeError):
        validate_url("ftp://news.example.com/file.txt")


def test_validate_url_ssrf_blocked():
    with pytest.raises(SSRFBlockedError):
        validate_url("http://127.0.0.1/admin")
    with pytest.raises(SSRFBlockedError):
        validate_url("http://169.254.169.254/latest/meta-data")


def test_normalize_url_strips_tracking():
    url = "https://news.example.com/article?utm_source=twitter&ref=123&id=45"
    normalized = normalize_url(url)
    assert "utm_source" not in normalized
    assert "ref" not in normalized
    assert "id=45" in normalized


def test_extract_domain():
    assert extract_domain("https://www.thehindu.com/news/national/") == "thehindu.com"
    assert extract_domain("https://bbc.co.uk/news") == "bbc.co.uk"


def test_url_to_hash():
    h1 = url_to_hash("https://example.com/news/")
    h2 = url_to_hash("https://EXAMPLE.COM/news")
    assert h1 == h2
