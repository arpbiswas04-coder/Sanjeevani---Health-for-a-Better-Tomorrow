"""Tests for recommendation confidence scoring."""

from __future__ import annotations

import pytest

from ai.recommendation_confidence.confidence import (
    calculate_calibration_evidence,
    calculate_confidence_score,
    calculate_interval_evidence,
    classify_confidence,
)
from ai.recommendation_confidence.config import (
    RecommendationConfidenceConfig,
)
from ai.recommendation_confidence.predict import (
    RecommendationConfidencePredictor,
    calculate_recommendation_confidence,
)


def test_interval_evidence_is_full_at_target() -> None:
    result = calculate_interval_evidence(
        interval_coverage=0.95,
        target_interval_coverage=0.95,
    )

    assert result == pytest.approx(1.0)


def test_interval_evidence_is_bounded() -> None:
    result = calculate_interval_evidence(
        interval_coverage=0.80,
        target_interval_coverage=0.95,
    )

    assert 0.0 < result < 1.0


def test_interval_evidence_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        calculate_interval_evidence(
            interval_coverage=1.1,
            target_interval_coverage=0.95,
        )


def test_calibration_evidence_is_full_for_low_error() -> None:
    result = calculate_calibration_evidence(
        calibration_error=0.02,
    )

    assert result == pytest.approx(1.0)


def test_calibration_evidence_is_zero_for_high_error() -> None:
    result = calculate_calibration_evidence(
        calibration_error=0.25,
    )

    assert result == pytest.approx(0.0)


def test_calibration_evidence_decreases_as_error_increases() -> None:
    low_error = calculate_calibration_evidence(0.08)
    high_error = calculate_calibration_evidence(0.15)

    assert low_error > high_error


def test_confidence_score_is_bounded() -> None:
    score = calculate_confidence_score(
        validation_score=0.90,
        interval_coverage=0.95,
        calibration_error=0.02,
    )

    assert 0.0 <= score <= 1.0


def test_strong_evidence_produces_high_confidence() -> None:
    score = calculate_confidence_score(
        validation_score=0.95,
        interval_coverage=0.95,
        calibration_error=0.02,
    )

    assert score >= 0.80
    assert classify_confidence(score) == "high"


def test_weak_evidence_produces_low_confidence() -> None:
    score = calculate_confidence_score(
        validation_score=0.40,
        interval_coverage=0.40,
        calibration_error=0.30,
    )

    assert score < 0.60
    assert classify_confidence(score) == "low"


def test_confidence_classification_boundaries() -> None:
    assert classify_confidence(0.80) == "high"
    assert classify_confidence(0.60) == "moderate"
    assert classify_confidence(0.59) == "low"


def test_predictor_returns_expected_response() -> None:
    predictor = RecommendationConfidencePredictor()

    result = predictor.predict(
        {
            "recommendation_id": "recommendation-001",
            "model_name": "patient-demand-model",
            "model_version": "v1",
            "validation_score": 0.90,
            "interval_coverage": 0.94,
            "target_interval_coverage": 0.95,
            "calibration_error": 0.04,
        }
    )

    assert result["success"] is True
    assert result["recommendation_id"] == "recommendation-001"
    assert result["model_name"] == "patient-demand-model"
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert result["confidence_level"] in {
        "low",
        "moderate",
        "high",
    }
    assert result["is_probability"] is False
    assert len(result["explanation"]) >= 1


def test_predictor_rejects_extra_fields() -> None:
    predictor = RecommendationConfidencePredictor()

    with pytest.raises(ValueError):
        predictor.predict(
            {
                "recommendation_id": "recommendation-001",
                "model_name": "patient-demand-model",
                "model_version": "v1",
                "validation_score": 0.90,
                "interval_coverage": 0.95,
                "target_interval_coverage": 0.95,
                "calibration_error": 0.03,
                "fake_confidence": 0.99,
            }
        )


def test_convenience_function_matches_predictor_contract() -> None:
    result = calculate_recommendation_confidence(
        recommendation_id="recommendation-002",
        model_name="bed-forecast-model",
        model_version="v1",
        validation_score=0.88,
        interval_coverage=0.93,
        calibration_error=0.05,
    )

    assert result["success"] is True
    assert result["recommendation_id"] == "recommendation-002"
    assert result["is_probability"] is False


def test_invalid_validation_score_is_rejected() -> None:
    predictor = RecommendationConfidencePredictor()

    with pytest.raises(ValueError):
        predictor.predict(
            {
                "recommendation_id": "recommendation-003",
                "model_name": "test-model",
                "model_version": "v1",
                "validation_score": 1.5,
                "interval_coverage": 0.95,
                "target_interval_coverage": 0.95,
                "calibration_error": 0.05,
            }
        )


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        RecommendationConfidenceConfig(
            validation_weight=0.8,
            interval_weight=0.3,
            calibration_weight=0.1,
        )


def test_confidence_score_uses_configured_weights() -> None:
    config = RecommendationConfidenceConfig(
        validation_weight=1.0,
        interval_weight=0.0,
        calibration_weight=0.0,
    )

    score = calculate_confidence_score(
        validation_score=0.73,
        interval_coverage=0.10,
        calibration_error=0.90,
        config=config,
    )

    assert score == pytest.approx(0.73)


def test_confidence_score_is_not_a_probability() -> None:
    result = calculate_recommendation_confidence(
        recommendation_id="recommendation-004",
        model_name="test-model",
        model_version="v1",
        validation_score=0.91,
        interval_coverage=0.95,
        calibration_error=0.03,
    )

    assert result["is_probability"] is False
    assert any(
        "not a probability" in message.lower()
        for message in result["explanation"]
    )