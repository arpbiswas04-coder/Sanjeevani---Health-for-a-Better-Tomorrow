"""Inference service for model explanations."""

from __future__ import annotations

from ai.common.base_model import BasePredictor

from .config import DEFAULT_CONFIG
from .features import calculate_attributions
from .schema import (
    ExplanationRequest,
    ExplanationResponse,
    FeatureContribution,
)


class ExplainabilityPredictor(BasePredictor):
    """Schema-validated feature attribution service."""

    def predict(self, payload: dict) -> dict:
        """Generate a transparent feature attribution response."""
        request = ExplanationRequest.model_validate(payload)

        contributions = calculate_attributions(
            request.features,
            baseline=0.0,
        )

        ranked = sorted(
            contributions,
            key=lambda item: abs(float(item["contribution"])),
            reverse=True,
        )[: DEFAULT_CONFIG.top_k]

        contribution_models = [
            FeatureContribution(**item)
            for item in ranked
        ]

        explanation = [
            (
                f"{item.feature} contributed "
                f"{item.contribution:.4f} "
                f"({item.direction})"
            )
            for item in contribution_models
        ]

        response = ExplanationResponse(
            success=True,
            model_version=DEFAULT_CONFIG.model_version,
            prediction=request.prediction,
            baseline=0.0,
            contributions=contribution_models,
            method="baseline_relative_attribution",
            explanation=explanation,
        )

        return response.model_dump()


def explain_prediction(payload: dict) -> dict:
    """Convenience explanation function."""
    return ExplainabilityPredictor().predict(payload)