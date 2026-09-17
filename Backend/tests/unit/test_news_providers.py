"""Unit tests verifying rate-limit tolerance across all news API providers."""
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from app.ingestion.providers import (
    CurrentsProvider,
    GNewsProvider,
    GuardianProvider,
    MediastackProvider,
    NewsDataProvider,
    NewsFlashProvider,
    SpaceflightProvider,
    TheNewsAPIProvider,
)


@pytest.mark.asyncio
async def test_newsdata_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = NewsDataProvider()
    provider.api_key = "test_key"

    # Must return empty list, not raise exception
    results = await provider.search("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_gnews_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = GNewsProvider()
    provider.api_key = "test_key"

    results = await provider.search_api("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_mediastack_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = MediastackProvider()
    provider.api_key = "test_key"

    results = await provider.search("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_currents_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = CurrentsProvider()
    provider.api_key = "test_key"

    results = await provider.search("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_thenewsapi_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = TheNewsAPIProvider()
    provider.api_key = "test_key"

    results = await provider.search("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_guardian_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = GuardianProvider()
    provider.api_key = "test_key"

    results = await provider.search("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_spaceflight_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = SpaceflightProvider()

    results = await provider.search("test", http_client=mock_client)
    assert results == []


@pytest.mark.asyncio
async def test_newsflash_provider_rate_limit_ignored():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    provider = NewsFlashProvider()
    provider.api_key = "test_key"

    results = await provider.search("test", http_client=mock_client)
    assert results == []
