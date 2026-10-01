"""Tests for composite healthcare risk scoring."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.common.types import RiskLevel
from ai.risk_scoring.config import (
    DEFAULT_CONFIG,
    RiskScoringConfig,
)
from ai.risk_scoring.data import records_to_dataframe
from ai.risk_scoring.evaluate import evaluate_risk_scores
from ai.risk_scoring.features import build_risk_features
from ai.risk_scoring.predict import RiskScoringPredictor, predict_risk
from ai.risk_scoring.schema import (
    RiskIndicatorRecord,
    RiskScoringRequest,
    RiskScoringResponse,
)
from ai.risk_scoring.train import (
    CompositeRiskScorer,
    train_risk_scorer,
)


def make_record(**overrides) -> RiskIndicatorRecord:
    """Create a valid risk indicator record."""
    data = {
        "timestamp": "2026-09-30T15:30:00Z",
        "supply_risk": 0.2,
        "bed_risk": 0.4,
        "workforce_risk": 0.3,
        "disease_risk": 0.1,
        "anomaly_risk": 0.2,
    }
    data.update(overrides)
    return RiskIndicatorRecord(**data)


def make_payload(**indicator_overrides) -> dict:
    """Create a valid prediction payload."""
    return {
        "facility_id": str(uuid.uuid4()),
        "indicators": make_record(
            **indicator_overrides
        ).model_dump(),
    }


class TestRiskSchemas:
    """Schema validation tests."""

    def test_valid_indicator_record(self):
        record = make_record()

        assert record.supply_risk == 0.2
        assert record.bed_risk == 0.4

    def test_invalid_risk_value_rejected(self):
        with pytest.raises(ValidationError):
            make_record(supply_risk=1.5)

    def test_negative_risk_value_rejected(self):
        with pytest.raises(ValidationError):
            make_record(bed_risk=-0.1)

    def test_invalid_timestamp_rejected(self):
        with pytest.raises(ValueError):
            make_record(timestamp="2026-09-30 15:30:00")

    def test_request_requires_uuid_v4(self):
        with pytest.raises(ValueError):
            RiskScoringRequest(
                facility_id="not-a-uuid",
                indicators=make_record(),
            )

    def test_response_schema_accepts_prediction(self):
        response = RiskScoringPredictor().predict(
            make_payload()
        )

        validated = RiskScoringResponse.model_validate(
            response
        )

        assert validated.success is True
        assert validated.coverage_ratio == 1.0


class TestRiskFeatures:
    """Feature construction tests."""

    def test_feature_columns_are_deterministic(self):
        records = [
            make_record(),
            make_record(
                timestamp="2026-10-01T15:30:00Z",
                bed_risk=0.5,
            ),
        ]

        frame = records_to_dataframe(records)
        features = build_risk_features(frame)

        assert list(features.columns) == [
            "supply_risk",
            "bed_risk",
            "workforce_risk",
            "disease_risk",
            "anomaly_risk",
        ]

    def test_feature_values_are_preserved(self):
        frame = records_to_dataframe(
            [make_record()]
        )

        features = build_risk_features(frame)

        assert features.iloc[0]["supply_risk"] == 0.2
        assert features.iloc[0]["bed_risk"] == 0.4


class TestRiskScorer:
    """Composite scoring tests."""

    def test_weights_sum_to_one(self):
        assert sum(DEFAULT_CONFIG.weights.values()) == pytest.approx(
            1.0
        )

    def test_composite_score(self):
        scorer = CompositeRiskScorer()

        result = scorer.calculate_score(
            {
                "supply_risk": 0.2,
                "bed_risk": 0.4,
                "workforce_risk": 0.3,
                "disease_risk": 0.1,
                "anomaly_risk": 0.2,
            }
        )

        assert result["risk_score"] == pytest.approx(0.25)
        assert result["resilience_score"] == pytest.approx(0.75)
        assert result["risk_level"] == "low"

    def test_critical_score(self):
        scorer = CompositeRiskScorer()

        result = scorer.calculate_score(
            {
                "supply_risk": 1.0,
                "bed_risk": 1.0,
                "workforce_risk": 1.0,
                "disease_risk": 1.0,
                "anomaly_risk": 1.0,
            }
        )

        assert result["risk_score"] == pytest.approx(1.0)
        assert result["resilience_score"] == pytest.approx(0.0)
        assert result["risk_level"] == "critical"

    def test_missing_indicator_rejected(self):
        scorer = CompositeRiskScorer()

        with pytest.raises(ValueError):
            scorer.calculate_score(
                {
                    "supply_risk": 0.2,
                    "bed_risk": 0.4,
                }
            )

    def test_out_of_range_indicator_rejected(self):
        scorer = CompositeRiskScorer()

        with pytest.raises(ValueError):
            scorer.calculate_score(
                {
                    "supply_risk": 1.2,
                    "bed_risk": 0.4,
                    "workforce_risk": 0.3,
                    "disease_risk": 0.1,
                    "anomaly_risk": 0.2,
                }
            )

    def test_non_finite_indicator_rejected(self):
        scorer = CompositeRiskScorer()

        with pytest.raises(ValueError):
            scorer.calculate_score(
                {
                    "supply_risk": float("nan"),
                    "bed_risk": 0.4,
                    "workforce_risk": 0.3,
                    "disease_risk": 0.1,
                    "anomaly_risk": 0.2,
                }
            )

    def test_training_factory_validates_weights(self):
        scorer = train_risk_scorer()

        assert isinstance(
            scorer,
            CompositeRiskScorer,
        )


class TestRiskEvaluation:
    """Evaluation tests."""

    def test_evaluation_returns_real_statistics(self):
        records = [
            make_record(),
            make_record(
                timestamp="2026-10-01T15:30:00Z",
                supply_risk=0.5,
            ),
        ]

        frame = records_to_dataframe(records)

        result = evaluate_risk_scores(frame)

        assert 0.0 <= result["mean_risk_score"] <= 1.0
        assert 0.0 <= result["min_risk_score"] <= 1.0
        assert 0.0 <= result["max_risk_score"] <= 1.0
        assert result["coverage_ratio"] == pytest.approx(1.0)


class TestRiskPrediction:
    """Inference tests."""

    def test_predictor_returns_expected_contract(self):
        result = RiskScoringPredictor().predict(
            make_payload()
        )

        assert result["success"] is True
        assert result["model_version"] == "risk-scoring-v1"
        assert result["risk_score"] == pytest.approx(0.25)
        assert result["resilience_score"] == pytest.approx(0.75)
        assert result["risk_level"] == RiskLevel.LOW
        assert len(result["components"]) == 5
        assert result["coverage_ratio"] == 1.0
        assert len(result["explanation"]) >= 1

    def test_contributions_sum_to_risk_score(self):
        result = predict_risk(make_payload())

        contribution_sum = sum(
            component["contribution"]
            for component in result["components"]
        )

        assert contribution_sum == pytest.approx(
            result["risk_score"]
        )

    def test_convenience_prediction_function(self):
        result = predict_risk(make_payload())

        assert result["success"] is True

    def test_high_risk_prediction(self):
        result = predict_risk(
            make_payload(
                supply_risk=0.9,
                bed_risk=0.9,
                workforce_risk=0.8,
                disease_risk=0.7,
                anomaly_risk=0.8,
            )
        )

        assert result["risk_level"] in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }
        assert result["risk_score"] > 0.75