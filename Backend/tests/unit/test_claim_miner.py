"""Unit tests for app.agents.claim_miner module."""
import pytest
from app.agents.claim_miner import ClaimMinerAgent


def test_find_source_span_exact_match():
    agent = ClaimMinerAgent()
    content = "Officials said 17 workers were injured in the industrial accident on Thursday."
    raw_text = "17 workers were injured"

    start, end = agent.find_source_span(content, raw_text)
    assert start is not None and end is not None
    assert content[start:end] == raw_text


def test_find_source_span_missing():
    agent = ClaimMinerAgent()
    content = "Officials said 17 workers were injured."
    raw_text = "50 people died"

    start, end = agent.find_source_span(content, raw_text)
    assert start is None
    assert end is None


@pytest.mark.asyncio
async def test_mine_claims_fallback():
    agent = ClaimMinerAgent()  # No LLM client passed -> uses deterministic fallback
    claims = await agent.mine_claims(
        article_id="art_1",
        event_id="evt_1",
        title="Accident in Chennai",
        content="Twelve workers were rescued after a wall collapse. Authorities arrived quickly.",
    )
    assert len(claims) > 0
    assert claims[0]["article_id"] == "art_1"
    assert claims[0]["event_id"] == "evt_1"
