"""Inference service for recommendation confidence."""

from __future__ import annotations

from ai.common.base_model import BasePredictor

from .confidence import calculate_confidence_score, classify_confidence
from .config import DEFAULT_CONFIG, RecommendationConfidenceConfig
from .schema import (
    ConfidenceEvidence,
    RecommendationConfidenceRequest,
    RecommendationConfidenceResponse,
)


class RecommendationConfidencePredictor(BasePredictor):
    """Generate transparent recommendation confidence scores."""

    def __init__(
        self,
        config: RecommendationConfidenceConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config

    def predict(self, payload: dict) -> dict:
        """Calculate confidence from model-quality evidence."""

        request = RecommendationConfidenceRequest.model_validate(payload)

        confidence_score = calculate_confidence_score(
            validation_score=request.validation_score,
            interval_coverage=request.interval_coverage,
            calibration_error=request.calibration_error,
            target_interval_coverage=request.target_interval_coverage,
            config=self.config,
        )

        confidence_level = classify_confidence(
            confidence_score,
            config=self.config,
        )

        evidence = ConfidenceEvidence(
            validation_score=request.validation_score,
            interval_coverage=request.interval_coverage,
            target_interval_coverage=request.target_interval_coverage,
            calibration_error=request.calibration_error,
        )

        explanation = [
            (
                f"Validation evidence: "
                f"{request.validation_score:.3f}."
            ),
            (
                f"Prediction interval coverage: "
                f"{request.interval_coverage:.3f} "
                f"against target {request.target_interval_coverage:.3f}."
            ),
            (
                f"Calibration error: "
                f"{request.calibration_error:.3f}."
            ),
            (
                "Confidence score is an evidence-based model-quality "
                "score, not a probability that the recommendation is correct."
            ),
        ]

        response = RecommendationConfidenceResponse(
            success=True,
            recommendation_id=request.recommendation_id,
            model_name=request.model_name,
            model_version=request.model_version,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            evidence=evidence,
            explanation=explanation,
            is_probability=False,
        )

        return response.model_dump()


def calculate_recommendation_confidence(
    *,
    recommendation_id: str,
    model_name: str,
    model_version: str,
    validation_score: float,
    interval_coverage: float,
    calibration_error: float,
    target_interval_coverage: float = (
        DEFAULT_CONFIG.target_interval_coverage
    ),
    config: RecommendationConfidenceConfig = DEFAULT_CONFIG,
) -> dict:
    """Convenience function for one-shot confidence calculation."""

    predictor = RecommendationConfidencePredictor(config=config)

    payload = {
        "recommendation_id": recommendation_id,
        "model_name": model_name,
        "model_version": model_version,
        "validation_score": validation_score,
        "interval_coverage": interval_coverage,
        "target_interval_coverage": target_interval_coverage,
        "calibration_error": calibration_error,
    }

    return predictor.predict(payload)