"""Training/calibration lifecycle for the deterministic risk scorer."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ai.common.base_model import BaseScorer

from .config import DEFAULT_CONFIG, RiskScoringConfig
from .features import RISK_COLUMNS


@dataclass
class CompositeRiskScorer(BaseScorer):
    """Weighted composite scorer for healthcare resilience indicators."""

    config: RiskScoringConfig = DEFAULT_CONFIG

    def calculate_score(self, features: dict[str, float]) -> dict[str, object]:
        """Calculate normalized risk and resilience scores."""
        missing = [
            column
            for column in RISK_COLUMNS
            if column not in features
        ]

        if missing:
            raise ValueError(f"Missing risk indicators: {missing}")

        values = {}

        for column in RISK_COLUMNS:
            value = float(features[column])

            if not np.isfinite(value):
                raise ValueError(f"{column} must be finite")

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{column} must be between 0 and 1"
                )

            values[column] = value

        weighted_score = sum(
            values[name] * self.config.weights[name]
            for name in RISK_COLUMNS
        )

        if weighted_score <= self.config.low_max:
            risk_level = "low"
        elif weighted_score <= self.config.moderate_max:
            risk_level = "moderate"
        elif weighted_score <= self.config.high_max:
            risk_level = "high"
        else:
            risk_level = "critical"

        return {
            "risk_score": float(weighted_score),
            "resilience_score": float(1.0 - weighted_score),
            "risk_level": risk_level,
        }


def train_risk_scorer(
    config: RiskScoringConfig = DEFAULT_CONFIG,
) -> CompositeRiskScorer:
    """Create the deterministic risk scorer."""
    total_weight = sum(config.weights.values())

    if not np.isclose(total_weight, 1.0):
        raise ValueError("Risk scoring weights must sum to 1.0")

    return CompositeRiskScorer(config=config)