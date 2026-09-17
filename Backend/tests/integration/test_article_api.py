"""Integration tests for Article and Source API endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.base import Base
from app.db.session import get_engine
from app.ingestion.article_extractor import ArticleExtractor, ExtractedArticle



@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    """Create fresh database tables before test run."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_sources_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Create source
        payload = {
            "name": "Reuters Wire",
            "domain": "reuters.com",
            "base_url": "https://www.reuters.com",
            "source_type": "WIRE",
            "language": "en"
        }
        res = await client.post("/api/v1/sources", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Reuters Wire"
        assert "id" in data

        # 2. List sources
        res_list = await client.get("/api/v1/sources")
        assert res_list.status_code == 200
        sources = res_list.json()
        assert len(sources) == 1
        assert sources[0]["domain"] == "reuters.com"


@pytest.mark.asyncio
async def test_ingest_url_and_article_detail():
    mock_extracted = ExtractedArticle(
        url="https://example.com/breaking-news",
        canonical_url="https://example.com/breaking-news",
        title="Major Energy Breakthrough",
        text="Scientists have developed a solar cell with 40 percent efficiency.",
        author="Alice Smith",
        published_date_str="2026-09-17T10:00:00Z",
        raw_html="<html><body>Mock HTML</body></html>",
        status_code=200,
        metadata={"paragraph_count": 1}
    )

    from app.api.v1.articles import service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        with patch.object(service.orchestrator.extractor, "extract_from_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extracted

            # 1. Ingest URL
            ingest_res = await client.post(
                "/api/v1/articles/ingest-url",
                json={"url": "https://example.com/breaking-news"}
            )
            assert ingest_res.status_code == 201


            art_data = ingest_res.json()
            assert art_data["title"] == "Major Energy Breakthrough"
            assert art_data["author"] == "Alice Smith"
            article_id = art_data["id"]

            # 2. List articles
            list_res = await client.get("/api/v1/articles")
            assert list_res.status_code == 200
            articles = list_res.json()
            assert len(articles) == 1
            assert articles[0]["id"] == article_id

            # 3. Get detailed article by ID
            detail_res = await client.get(f"/api/v1/articles/{article_id}")
            assert detail_res.status_code == 200
            detail_data = detail_res.json()
            assert "40 percent efficiency" in detail_data["content"]
