"""Unit tests for app.analysis modules and DriftInvestigatorAgent."""
import pytest
from app.analysis.numbers import check_numerical_drift, extract_numbers_from_text
from app.analysis.source_overlap import analyze_source_overlap, calculate_jaccard_similarity
from app.agents.drift_investigator import DriftInvestigatorAgent
from app.core.constants import RelationType


def test_extract_numbers():
    text = "Initial report said 17 injured, later revised to 12.0 with $50,000 damage."
    nums = extract_numbers_from_text(text)
    assert 17.0 in nums
    assert 12.0 in nums
    assert 50000.0 in nums


def test_check_numerical_drift():
    # 17 -> 20 (Drift)
    res1 = check_numerical_drift(17, 20)
    assert res1["has_drift"] is True
    assert res1["direction"] == "INCREASE"

    # 17 -> 17 (No drift)
    res2 = check_numerical_drift(17, 17)
    assert res2["has_drift"] is False


def test_analyze_source_overlap():
    s1 = "Officials reported that 17 workers were injured in a factory explosion on Thursday morning."
    s2 = "Officials reported that 17 workers were injured in a factory explosion on Thursday morning."

    overlap = analyze_source_overlap(s1, s2)
    assert overlap["jaccard_similarity"] == 1.0
    assert overlap["assessment"] == "HIGH_SOURCE_DEPENDENCE"


@pytest.mark.asyncio
async def test_investigate_claim_drift_fallback():
    agent = DriftInvestigatorAgent()
    source_claims = [
        {"id": "c1", "subject": "workers", "predicate": "injured", "object_value": "17", "attribution": "officials"}
    ]
    target_claims = [
        {"id": "c2", "subject": "workers", "predicate": "injured", "object_value": "20", "attribution": None}
    ]

    relations = await agent.investigate_claim_drift(source_claims, target_claims)
    assert len(relations) == 1
    assert relations[0]["relation_type"] == RelationType.NUMERICAL_DRIFT
