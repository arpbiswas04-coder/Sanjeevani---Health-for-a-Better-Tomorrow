"""Inference service for model performance and drift monitoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.common.base_model import BasePredictor

from .config import DEFAULT_CONFIG, ModelMonitoringConfig
from .data import validate_feature_mapping, validate_numeric_series
from .evaluate import (
    calculate_feature_drift,
    calculate_performance_degradation,
    calculate_prediction_drift,
    should_retrain,
)
from .schema import (
    ModelMonitoringRequest,
    ModelMonitoringResponse,
    PerformanceMetrics,
)
from .train import MonitoringBaseline, train_monitoring_baseline


class ModelMonitoringPredictor(BasePredictor):
    """Monitor feature, prediction, and model-performance drift."""

    def __init__(
        self,
        config: ModelMonitoringConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config
        self.baseline: MonitoringBaseline | None = None

    def fit(
        self,
        reference_features: Mapping[str, Sequence[float]],
        reference_predictions: Sequence[float],
        reference_performance: PerformanceMetrics | None = None,
    ) -> MonitoringBaseline:
        """Create and store the monitoring baseline."""
        self.baseline = train_monitoring_baseline(
            reference_features=reference_features,
            reference_predictions=reference_predictions,
            reference_performance=reference_performance,
            config=self.config,
        )
        return self.baseline

    def predict(self, payload: dict) -> dict:
        """Evaluate current model behavior against the stored baseline."""
        if self.baseline is None:
            raise RuntimeError(
                "Model monitoring baseline has not been fitted."
            )

        request = ModelMonitoringRequest.model_validate(payload)

        current_features = validate_feature_mapping(
            request.current_features,
            min_size=self.config.min_sample_size,
        )

        current_predictions = validate_numeric_series(
            request.current_predictions,
            name="current_predictions",
            min_size=self.config.min_sample_size,
        )

        # Compare current feature distributions with the reference baseline.
        drift_metrics = calculate_feature_drift(
            self.baseline.reference_features,
            current_features,
            config=self.config,
        )

        # Compare current prediction distribution with the reference baseline.
        prediction_drift = calculate_prediction_drift(
            self.baseline.reference_predictions,
            current_predictions,
            config=self.config,
        )

        drift_metrics.extend(prediction_drift)

        # Compare model performance when both reference and current
        # performance metrics are available.
        performance_degradation: dict[str, float] = {}

        if (
            self.baseline.reference_performance is not None
            and request.current_performance is not None
        ):
            performance_degradation = calculate_performance_degradation(
                self.baseline.reference_performance,
                request.current_performance,
                threshold=self.config.performance_degradation_threshold,
            )

        retraining_recommended = should_retrain(
            drift_metrics,
            performance_degradation,
            config=self.config,
        )

        has_critical_drift = any(
            metric.status == "critical"
            for metric in drift_metrics
        )

        has_warning_drift = any(
            metric.status == "warning"
            for metric in drift_metrics
        )

        has_performance_degradation = any(
            value >= self.config.performance_degradation_threshold
            for value in performance_degradation.values()
        )

        if has_critical_drift or has_performance_degradation:
            overall_status = "critical"
        elif has_warning_drift:
            overall_status = "warning"
        else:
            overall_status = "stable"

        explanation = [
            f"Monitored model: {request.model_name}.",
            f"Reference model version: {request.model_version}.",
            f"Current prediction sample count: {len(current_predictions)}.",
        ]

        if retraining_recommended:
            explanation.append(
                "Retraining is recommended because a configured "
                "monitoring threshold was crossed."
            )
        else:
            explanation.append(
                "No configured retraining threshold was crossed."
            )

        response = ModelMonitoringResponse(
            success=True,
            model_name=request.model_name,
            model_version=request.model_version,
            overall_status=overall_status,
            drift_metrics=drift_metrics,
            performance_degradation=performance_degradation,
            retraining_recommended=retraining_recommended,
            explanation=explanation,
        )

        return response.model_dump()


def monitor_model(
    reference_features: Mapping[str, Sequence[float]],
    current_features: Mapping[str, Sequence[float]],
    reference_predictions: Sequence[float],
    current_predictions: Sequence[float],
    *,
    model_name: str,
    model_version: str,
    reference_performance: PerformanceMetrics | None = None,
    current_performance: PerformanceMetrics | None = None,
    config: ModelMonitoringConfig = DEFAULT_CONFIG,
) -> dict:
    """Convenience function for one-shot model monitoring."""
    predictor = ModelMonitoringPredictor(config=config)

    predictor.fit(
        reference_features=reference_features,
        reference_predictions=reference_predictions,
        reference_performance=reference_performance,
    )

    payload = {
        "model_name": model_name,
        "model_version": model_version,
        "reference_features": dict(reference_features),
        "current_features": dict(current_features),
        "reference_predictions": list(reference_predictions),
        "current_predictions": list(current_predictions),
        "reference_performance": (
            reference_performance.model_dump()
            if reference_performance is not None
            else None
        ),
        "current_performance": (
            current_performance.model_dump()
            if current_performance is not None
            else None
        ),
    }

    return predictor.predict(payload)