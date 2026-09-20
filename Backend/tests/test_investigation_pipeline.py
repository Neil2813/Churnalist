"""
Test suite for Churnalist Trace a Story investigation pipeline.
"""
from __future__ import annotations

import asyncio
import pytest
from datetime import datetime, timezone

from app.analysis.inconsistency import InconsistencyDetector
from app.ingestion.async_fetcher import BoundedAsyncFetcher
from app.retrieval.candidate_retriever import CandidateRetriever
from app.services.event_context_service import EventContext, EventContextService


def test_ssrf_protection():
    """Verify that private IP ranges and localhost URLs are blocked."""
    fetcher = BoundedAsyncFetcher()

    with pytest.raises(ValueError, match="forbidden"):
        fetcher.validate_url("http://127.0.0.1/admin")

    with pytest.raises(ValueError, match="forbidden"):
        fetcher.validate_url("http://localhost/secret")

    with pytest.raises(ValueError, match="forbidden"):
        fetcher.validate_url("http://169.254.169.254/latest/meta-data/")

    # Public scheme validation
    with pytest.raises(ValueError, match="scheme"):
        fetcher.validate_url("file:///etc/passwd")


def test_casualty_independent_candidate_matching():
    """Verify that 17 dead vs 20 dead yields high candidate match score."""
    retriever = CandidateRetriever()
    now = datetime.now(timezone.utc)

    context = EventContext(
        incident_title="Avinashi bus crash",
        incident_type="bus crash",
        locations=["Avinashi", "Tamil Nadu"],
        organizations=["KSRTC"],
        anchor_timestamp=now,
        distinctive_headline_terms=["KSRTC", "bus", "crash", "Avinashi"],
    )

    candidate_17 = {
        "title": "17 killed in Avinashi KSRTC bus crash in Tamil Nadu",
        "snippet": "At least 17 passengers died when a KSRTC bus collided near Avinashi.",
        "url": "https://example.com/article-17",
        "published_at": now.isoformat(),
    }

    candidate_20 = {
        "title": "20 killed in Tamil Nadu bus accident near Avinashi",
        "snippet": "The death toll in the KSRTC bus crash near Avinashi rose to 20.",
        "url": "https://example.com/article-20",
        "published_at": now.isoformat(),
    }

    score_17 = retriever.score_candidate(candidate_17, context)
    score_20 = retriever.score_candidate(candidate_20, context)

    assert score_17 > 0.5, f"Expected candidate 17 score > 0.5, got {score_17}"
    assert score_20 > 0.5, f"Expected candidate 20 score > 0.5, got {score_20}"


def test_internal_inconsistency_detection():
    """Verify Headline: 20 dead vs Body: 19 dead triggers INTERNAL_SOURCE_INCONSISTENCY."""
    detector = InconsistencyDetector()

    headline = "20 dead in Avinashi bus crash"
    body = "At least 19 dead after a KSRTC bus collided with a container truck near Avinashi."

    items = detector.check_article(
        article_id="art_test",
        event_id="evt_test",
        headline=headline,
        body=body,
    )

    assert len(items) == 1
    assert items[0]["inconsistency_type"] == "INTERNAL_SOURCE_INCONSISTENCY"
    assert "20" in items[0]["headline_claim"]
    assert "19" in items[0]["body_claim"]


def test_event_context_query_generation():
    """Verify generated search queries omit casualty numbers."""
    service = EventContextService()
    now = datetime.now(timezone.utc)

    context = EventContext(
        incident_title="KSRTC bus crash near Avinashi kills 17",
        incident_type="bus crash",
        locations=["Avinashi", "Tamil Nadu"],
        organizations=["KSRTC"],
        anchor_timestamp=now,
        distinctive_headline_terms=["KSRTC", "bus", "crash", "Avinashi"],
    )

    queries = service.generate_search_queries(context)
    assert len(queries) > 0
    for q in queries:
        assert "17" not in q, f"Query '{q}' should not contain mandatory casualty number 17"
