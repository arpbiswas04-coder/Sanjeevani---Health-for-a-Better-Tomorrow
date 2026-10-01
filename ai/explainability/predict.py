"""Prediction and inference helpers for model explainability."""

from __future__ import annotations

from typing import Any, Mapping

from ai.common.base_model import BasePredictor
from ai.explainability.config import DEFAULT_CONFIG
from ai.explainability.data import validate_features
from ai.explainability.features import calculate_attributions
from ai.explainability.schema import ExplanationRequest


class ExplainabilityPredictor(BasePredictor):
    """Generate feature-level explanations for predictions.

    A tree-based model can be supplied at runtime. When supplied,
    SHAP TreeExplainer is used. Without a model, the deterministic
    baseline-relative attribution remains available for compatibility.
    """

    def __init__(self, model: Any | None = None) -> None:
        self.model = model

    def predict(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Generate an explanation for a prediction payload."""
        request = ExplanationRequest.model_validate(payload)
        features = validate_features(request.features)

        contributions = calculate_attributions(
            features,
            baseline=0.0,
            model=self.model,
        )

        contributions = sorted(
            contributions,
            key=lambda item: abs(float(item["contribution"])),
            reverse=True,
        )[: DEFAULT_CONFIG.top_k]

        method = (
            "shap_tree_explainer"
            if self.model is not None
            else "baseline_relative_attribution"
        )

        explanation = [
            (
                f"{item['feature']}: "
                f"{item['direction']} contribution "
                f"({float(item['contribution']):.6f})"
            )
            for item in contributions
        ]

        return {
            "success": True,
            "model_version": DEFAULT_CONFIG.model_version,
            "prediction": request.prediction,
            "baseline": 0.0,
            "contributions": contributions,
            "method": method,
            "explanation": explanation,
        }


def explain_prediction(
    payload: Mapping[str, Any],
    model: Any | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for explanation inference."""
    return ExplainabilityPredictor(model=model).predict(payload)