"""Training and baseline management for model monitoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from ai.common.base_model import BasePredictor

from .config import DEFAULT_CONFIG, ModelMonitoringConfig
from .data import validate_feature_mapping, validate_numeric_series
from .schema import PerformanceMetrics


class MonitoringBaseline:
    """Stores validated reference distributions and performance metrics."""

    def __init__(
        self,
        *,
        reference_features: Mapping[str, Sequence[float]],
        reference_predictions: Sequence[float],
        reference_performance: PerformanceMetrics | None = None,
        config: ModelMonitoringConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config

        self.reference_features = validate_feature_mapping(
            reference_features,
            min_size=config.min_sample_size,
        )

        self.reference_predictions = validate_numeric_series(
            reference_predictions,
            name="reference_predictions",
            min_size=config.min_sample_size,
        )

        self.reference_performance = reference_performance


def train_monitoring_baseline(
    *,
    reference_features: Mapping[str, Sequence[float]],
    reference_predictions: Sequence[float],
    reference_performance: PerformanceMetrics | None = None,
    config: ModelMonitoringConfig = DEFAULT_CONFIG,
) -> MonitoringBaseline:
    """Create a validated monitoring baseline."""
    return MonitoringBaseline(
        reference_features=reference_features,
        reference_predictions=reference_predictions,
        reference_performance=reference_performance,
        config=config,
    )


class ModelMonitoringTrainer(BasePredictor):
    """Base-compatible wrapper for creating monitoring baselines."""

    def __init__(
        self,
        config: ModelMonitoringConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config
        self.baseline: MonitoringBaseline | None = None

    def fit(
        self,
        *,
        reference_features: Mapping[str, Sequence[float]],
        reference_predictions: Sequence[float],
        reference_performance: PerformanceMetrics | None = None,
    ) -> MonitoringBaseline:
        """Fit the monitoring baseline."""
        self.baseline = train_monitoring_baseline(
            reference_features=reference_features,
            reference_predictions=reference_predictions,
            reference_performance=reference_performance,
            config=self.config,
        )
        return self.baseline

    def predict(self, payload: dict) -> dict:
        """Return baseline metadata for compatibility with BasePredictor."""
        if self.baseline is None:
            raise RuntimeError("Monitoring baseline has not been fitted.")

        return {
            "model_version": self.config.model_version,
            "feature_count": len(self.baseline.reference_features),
            "prediction_sample_count": len(
                self.baseline.reference_predictions
            ),
        }