"""
Unit and regression tests for Multilingual Claim Drift Detection across
English, Hindi, Tamil, Telugu, and Bengali.
"""
import pytest
from app.analysis.drift import classify_claim_relation, detect_severity_change, detect_attribution_loss
from app.analysis.language import detect_correction_language_signal
from app.core.constants import RelationType


def test_tamil_numerical_drift():
    """Verify English (17) -> Tamil (~20) numerical drift detection."""
    source_claim = {
        "id": "c_en_1",
        "subject": "people",
        "predicate": "injured",
        "object_value": "17",
        "extracted_value": "17",
        "original_language": "en",
        "original_text": "Officials said 17 people were injured.",
        "english_translation": "Officials said 17 people were injured.",
        "raw_text": "Officials said 17 people were injured.",
        "attribution": "officials",
    }
    target_claim = {
        "id": "c_ta_1",
        "subject": "people",
        "predicate": "injured",
        "object_value": "around 20",
        "extracted_value": "~20",
        "original_language": "ta",
        "original_text": "சுமார் 20 பேர் காயமடைந்தனர்.",
        "english_translation": "Around 20 people were injured.",
        "raw_text": "சுமார் 20 பேர் காயமடைந்தனர்.",
        "attribution": None,
    }

    result = classify_claim_relation(source_claim, target_claim)

    assert result["relation_type"] == RelationType.NUMERICAL_DRIFT
    assert result["evidence"]["source_extracted_value"] == "17"
    assert result["evidence"]["target_extracted_value"] == "~20"
    assert result["evidence"]["numeric"]["has_drift"] is True
    assert result["evidence"]["numeric"]["direction"] == "INCREASE"
    assert "17" in result["reason"] and "20" in result["reason"]


def test_bengali_severity_amplification():
    """Verify English (injured) -> Bengali (seriously injured) severity amplification."""
    source_claim = {
        "id": "c_en_2",
        "subject": "workers",
        "predicate": "injured",
        "object_value": "several",
        "extracted_value": "several",
        "original_language": "en",
        "original_text": "Workers were injured in the factory incident.",
        "english_translation": "Workers were injured in the factory incident.",
        "raw_text": "Workers were injured in the factory incident.",
    }
    target_claim = {
        "id": "c_bn_2",
        "subject": "workers",
        "predicate": "injured",
        "object_value": "several",
        "extracted_value": "several",
        "original_language": "bn",
        "original_text": "বেশ কয়েকজন শ্রমিক গুরুতর আহত হয়েছেন।",
        "english_translation": "Several workers were seriously injured in the factory incident.",
        "raw_text": "বেশ কয়েকজন শ্রমিক গুরুতর আহত হয়েছেন।",
    }

    result = classify_claim_relation(source_claim, target_claim)

    assert result["relation_type"] == RelationType.SEVERITY_AMPLIFICATION
    assert result["evidence"]["severity"]["has_change"] is True
    assert result["evidence"]["severity"]["direction"] == "AMPLIFICATION"
    assert result["evidence"]["severity"]["source_level"] == "injured"
    assert result["evidence"]["severity"]["target_level"] == "seriously injured"


def test_non_numeric_values_no_crash():
    """Ensure non-numeric extracted_values like 'several', 'many', 'unknown' never crash."""
    test_cases = [
        ("17", "several"),
        ("several", "many"),
        ("many", "17"),
        ("unknown", "unknown"),
        (None, "several"),
    ]

    for val1, val2 in test_cases:
        src = {
            "id": "s1",
            "subject": "workers",
            "predicate": "affected",
            "object_value": str(val1),
            "extracted_value": val1,
            "raw_text": f"Workers affected count: {val1}",
            "english_translation": f"Workers affected count: {val1}",
        }
        tgt = {
            "id": "t1",
            "subject": "workers",
            "predicate": "affected",
            "object_value": str(val2),
            "extracted_value": val2,
            "raw_text": f"Workers affected count: {val2}",
            "english_translation": f"Workers affected count: {val2}",
        }
        # Must execute without exception
        res = classify_claim_relation(src, tgt)
        assert isinstance(res, dict)
        assert "relation_type" in res
        assert "reason" in res


def test_cross_language_correction_detection():
    """Verify detection of correction keywords across English, Hindi, Tamil, Telugu, and Bengali."""
    # English
    assert detect_correction_language_signal("Official update: A correction was issued by authorities.", "en") is True
    # Hindi
    assert detect_correction_language_signal("घटना पर अधिकारियों ने सुधार जारी किया।", "hi") is True
    assert detect_correction_language_signal("संख्या में संशोधन किया गया।", "hi") is True
    # Tamil
    assert detect_correction_language_signal("காயமடைந்தோர் எண்ணிக்கையில் திருத்தம் வெளியிடப்பட்டது.", "ta") is True
    assert detect_correction_language_signal("செய்தி புதுப்பிக்கப்பட்டது.", "ta") is True
    # Telugu
    assert detect_correction_language_signal("ప్రభుత్వ నివేదికలో సవరణ ప్రకటించారు.", "te") is True
    assert detect_correction_language_signal("తాజా సమాచారం నవీకరించబడింది.", "te") is True
    # Bengali
    assert detect_correction_language_signal("প্রতিবেদনে তথ্য সংশোধন করা হয়েছে।", "bn") is True
    assert detect_correction_language_signal("আহতদের সংখ্যা নিয়ে নতুন আপডেট প্রকাশ।", "bn") is True
    # Kannada
    assert detect_correction_language_signal("ವರದಿಯಲ್ಲಿ ತಿದ್ದುಪಡಿ ಪ್ರಕಟಿಸಲಾಗಿದೆ.", "kn") is True
    assert detect_correction_language_signal("ಸುದ್ದಿ ನವೀಕರಿಸಲಾಗಿದೆ.", "kn") is True
    assert detect_correction_language_signal("ಪೊಲೀಸ್ ಇಲಾಖೆಯಿಂದ ಸ್ಪಷ್ಟೀಕರಣ ನೀಡಲಾಗಿದೆ.", "kn") is True
    # Negative test (standard report with no correction words)
    assert detect_correction_language_signal("The train departed at 8 am heading north.", "en") is False
    assert detect_correction_language_signal("ரயில் காலையில் புறப்பட்டது.", "ta") is False
    assert detect_correction_language_signal("ರೈಲು ಬೆಳಿಗ್ಗೆ ಹೊರಟಿತು.", "kn") is False


def test_attribution_loss_cross_language():
    """Verify attribution loss detection from English to Hindi."""
    source_claim = {
        "id": "s_attr",
        "subject": "people",
        "predicate": "injured",
        "object_value": "17",
        "extracted_value": "17",
        "attribution": "officials said",
        "original_language": "en",
        "original_text": "Officials said 17 people were injured.",
        "english_translation": "Officials said 17 people were injured.",
        "raw_text": "Officials said 17 people were injured.",
    }
    target_claim = {
        "id": "t_attr",
        "subject": "people",
        "predicate": "injured",
        "object_value": "17",
        "extracted_value": "17",
        "attribution": None,
        "original_language": "hi",
        "original_text": "17 लोग घायल हो गए।",
        "english_translation": "17 people were injured.",
        "raw_text": "17 लोग घायल हो गए।",
    }

    res = classify_claim_relation(source_claim, target_claim)
    assert res["relation_type"] == RelationType.ATTRIBUTION_LOSS
    assert "attribution" in res["reason"].lower()


def test_english_unchanged_regression_baseline():
    """
    Direct regression test comparing English-only inputs against pre-change baseline:
    Ensures pre-change baseline output is identical.
    """
    source_claim = {
        "id": "c1",
        "subject": "workers",
        "predicate": "injured",
        "object_value": "17",
        "raw_text": "Officials said 17 workers were injured.",
        "attribution": "officials",
    }
    target_claim_drift = {
        "id": "c2",
        "subject": "workers",
        "predicate": "injured",
        "object_value": "20",
        "raw_text": "20 workers were injured.",
        "attribution": None,
    }
    target_claim_attr_loss = {
        "id": "c3",
        "subject": "workers",
        "predicate": "injured",
        "object_value": "17",
        "raw_text": "17 workers were injured.",
        "attribution": None,
    }

    # Baseline 1: Numerical drift
    res1 = classify_claim_relation(source_claim, target_claim_drift)
    assert res1["relation_type"] == RelationType.NUMERICAL_DRIFT
    assert res1["confidence"] == 0.90
    assert res1["reason"] == "Numeric value changed from 17 to 20."

    # Baseline 2: Attribution loss
    res2 = classify_claim_relation(source_claim, target_claim_attr_loss)
    assert res2["relation_type"] == RelationType.ATTRIBUTION_LOSS
    assert res2["confidence"] == 0.80
    assert res2["reason"] == "Source attribution dropped in the target claim."
