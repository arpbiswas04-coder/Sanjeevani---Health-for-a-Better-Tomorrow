"""Tests for model explainability."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.explainability.data import (
    features_to_dataframe,
    validate_features,
)
from ai.explainability.evaluate import evaluate_explanations
from ai.explainability.features import calculate_attributions
from ai.explainability.predict import (
    ExplainabilityPredictor,
    explain_prediction,
)
from ai.explainability.schema import (
    ExplanationRequest,
    ExplanationResponse,
)
from ai.explainability.train import (
    ExplainabilityModel,
    train_explainability_model,
)


def sample_features() -> dict[str, float]:
    """Return deterministic test features."""
    return {
        "bed_risk": 0.4,
        "supply_risk": 0.2,
        "disease_risk": 0.1,
        "workforce_risk": 0.3,
        "anomaly_risk": 0.2,
    }


class TestExplainabilitySchema:
    """Schema validation tests."""

    def test_valid_request(self):
        request = ExplanationRequest(
            prediction=0.8,
            features=sample_features(),
        )

        assert request.prediction == 0.8
        assert len(request.features) == 5

    def test_empty_features_rejected(self):
        with pytest.raises(ValidationError):
            ExplanationRequest(
                prediction=0.8,
                features={},
            )

    def test_extra_request_field_rejected(self):
        with pytest.raises(ValidationError):
            ExplanationRequest(
                prediction=0.8,
                features=sample_features(),
                unexpected=1,
            )

    def test_response_schema(self):
        result = explain_prediction(
            {
                "prediction": 0.8,
                "features": sample_features(),
            }
        )

        response = ExplanationResponse.model_validate(result)

        assert response.success is True
        assert response.method == "baseline_relative_attribution"


class TestExplainabilityData:
    """Input validation tests."""

    def test_validate_features(self):
        result = validate_features(sample_features())

        assert result == sample_features()

    def test_empty_features_rejected(self):
        with pytest.raises(ValueError):
            validate_features({})

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            validate_features(
                {
                    "feature_a": float("nan"),
                }
            )

    def test_infinity_rejected(self):
        with pytest.raises(ValueError):
            validate_features(
                {
                    "feature_a": float("inf"),
                }
            )

    def test_dataframe_conversion(self):
        frame = features_to_dataframe(sample_features())

        assert frame.shape == (1, 5)
        assert list(frame.columns) == list(
            sample_features().keys()
        )


class TestFeatureAttribution:
    """Attribution calculation tests."""

    def test_attributions_are_deterministic(self):
        first = calculate_attributions(
            sample_features()
        )
        second = calculate_attributions(
            sample_features()
        )

        assert first == second

    def test_zero_features_have_zero_contribution(self):
        result = calculate_attributions(
            {
                "a": 0.0,
                "b": 0.0,
            }
        )

        assert all(
            item["contribution"] == 0.0
            for item in result
        )

    def test_positive_features_are_positive(self):
        result = calculate_attributions(
            {
                "a": 0.2,
                "b": 0.8,
            }
        )

        assert all(
            item["direction"] == "positive"
            for item in result
        )

    def test_negative_feature_is_negative(self):
        result = calculate_attributions(
            {
                "positive": 0.5,
                "negative": -0.2,
            }
        )

        negative = next(
            item
            for item in result
            if item["feature"] == "negative"
        )

        assert negative["direction"] == "negative"
        assert negative["contribution"] < 0


class TestExplainabilityTraining:
    """Training/baseline tests."""

    def test_training_returns_model(self):
        model = train_explainability_model(
            [
                {"a": 0.2, "b": 0.4},
                {"a": 0.3, "b": 0.5},
            ],
            [0.6, 0.8],
        )

        assert isinstance(
            model,
            ExplainabilityModel,
        )
        assert model.baseline == pytest.approx(0.7)

    def test_mismatched_lengths_rejected(self):
        with pytest.raises(ValueError):
            train_explainability_model(
                [{"a": 0.2}],
                [0.5, 0.6],
            )

    def test_empty_training_data_rejected(self):
        with pytest.raises(ValueError):
            train_explainability_model(
                [],
                [],
            )


class TestExplainabilityEvaluation:
    """Explanation evaluation tests."""

    def test_complete_attribution(self):
        result = evaluate_explanations(
            {
                "a": 0.2,
                "b": 0.4,
            },
            prediction=0.6,
            baseline=0.7,
        )

        assert result["is_complete"] == 1.0
        assert result["completeness_error"] < 1e-10

    def test_target_delta_is_reported(self):
        result = evaluate_explanations(
            {
                "a": 0.2,
                "b": 0.4,
            },
            prediction=0.6,
            baseline=0.7,
        )

        assert result["target_delta"] == pytest.approx(-0.1)


class TestExplainabilityPrediction:
    """Inference tests."""

    def test_prediction_contract(self):
        result = ExplainabilityPredictor().predict(
            {
                "prediction": 0.8,
                "features": sample_features(),
            }
        )

        assert result["success"] is True
        assert result["model_version"] == "explainability-v1"
        assert result["prediction"] == 0.8
        assert result["baseline"] == 0.0
        assert len(result["contributions"]) == 5

    def test_top_k_is_applied(self):
        features = {
            "a": 0.5,
            "b": 0.4,
            "c": 0.3,
            "d": 0.2,
            "e": 0.1,
            "f": 0.05,
            "g": 0.01,
        }

        result = explain_prediction(
            {
                "prediction": 1.0,
                "features": features,
            }
        )

        assert len(result["contributions"]) == 5

    def test_contributions_are_ranked(self):
        result = explain_prediction(
            {
                "prediction": 0.8,
                "features": sample_features(),
            }
        )

        contributions = [
            abs(item["contribution"])
            for item in result["contributions"]
        ]

        assert contributions == sorted(
            contributions,
            reverse=True,
        )

    def test_explanation_text_matches_features(self):
        result = explain_prediction(
            {
                "prediction": 0.8,
                "features": sample_features(),
            }
        )

        assert len(result["explanation"]) == 5
        assert "bed_risk" in result["explanation"][0]