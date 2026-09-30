"""Inference service for composite healthcare resilience scoring."""

from __future__ import annotations

import uuid

from ai.common.base_model import BasePredictor
from ai.common.types import RiskLevel, now_utc_iso8601

from .config import DEFAULT_CONFIG
from .schema import (
    RiskComponent,
    RiskScoringRequest,
    RiskScoringResponse,
)
from .train import CompositeRiskScorer


class RiskScoringPredictor(BasePredictor):
    """Schema-validated composite resilience risk predictor."""

    def __init__(
        self,
        scorer: CompositeRiskScorer | None = None,
    ) -> None:
        self.scorer = scorer or CompositeRiskScorer()

    def predict(self, payload: dict) -> dict:
        """Validate request and calculate the composite risk score."""
        request = RiskScoringRequest.model_validate(payload)

        indicator_values = request.indicators.model_dump(
            exclude={"timestamp"},
        )

        result = self.scorer.calculate_score(indicator_values)

        components = [
            RiskComponent(
                name=name,
                value=float(indicator_values[name]),
                weight=float(self.scorer.config.weights[name]),
                contribution=float(
                    indicator_values[name]
                    * self.scorer.config.weights[name]
                ),
            )
            for name in self.scorer.config.weights
        ]

        response = RiskScoringResponse(
            success=True,
            prediction_id=str(uuid.uuid4()),
            facility_id=request.facility_id,
            model_version=DEFAULT_CONFIG.model_version,
            generated_at=now_utc_iso8601(),
            resilience_score=float(result["resilience_score"]),
            risk_score=float(result["risk_score"]),
            risk_level=RiskLevel(result["risk_level"]),
            components=components,
            coverage_ratio=1.0,
            explanation=[
                "Composite score is calculated from the configured "
                "weighted risk indicators.",
                f"Highest contributing indicator: "
                f"{max(components, key=lambda item: item.contribution).name}.",
            ],
        )

        return response.model_dump()


def predict_risk(payload: dict) -> dict:
    """Convenience inference function."""
    return RiskScoringPredictor().predict(payload)