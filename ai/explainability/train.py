"""Explainability preparation and baseline calculation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import DEFAULT_CONFIG, ExplainabilityConfig
from .data import validate_features


@dataclass
class ExplainabilityModel:
    """Lightweight explanation baseline."""

    config: ExplainabilityConfig = DEFAULT_CONFIG
    baseline: float = 0.0

    def fit(
        self,
        feature_rows: list[dict[str, float]],
        predictions: list[float],
    ) -> "ExplainabilityModel":
        """Fit the explanation baseline from observed predictions."""
        if not feature_rows:
            raise ValueError("At least one feature row is required")

        if len(feature_rows) != len(predictions):
            raise ValueError(
                "feature_rows and predictions must have equal length"
            )

        validated_predictions = np.asarray(
            predictions,
            dtype=float,
        )

        if not np.isfinite(validated_predictions).all():
            raise ValueError("Predictions must be finite")

        for row in feature_rows:
            validate_features(row)

        self.baseline = float(validated_predictions.mean())
        return self


def train_explainability_model(
    feature_rows: list[dict[str, float]],
    predictions: list[float],
    config: ExplainabilityConfig = DEFAULT_CONFIG,
) -> ExplainabilityModel:
    """Fit the explanation baseline."""
    return ExplainabilityModel(config=config).fit(
        feature_rows,
        predictions,
    )