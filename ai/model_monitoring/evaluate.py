"""Evaluation logic for model performance and drift monitoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.common.metrics import (
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    calculate_wape,
)

from .config import DEFAULT_CONFIG, ModelMonitoringConfig
from .data import validate_feature_mapping, validate_numeric_series
from .features import calculate_ks, calculate_psi, classify_ks, classify_psi
from .schema import DriftMetric, PerformanceMetrics


def calculate_performance_metrics(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> PerformanceMetrics:
    """Calculate regression performance metrics."""
    actual_values = validate_numeric_series(
        actual,
        name="actual",
        min_size=1,
    )
    predicted_values = validate_numeric_series(
        predicted,
        name="predicted",
        min_size=1,
    )

    if len(actual_values) != len(predicted_values):
        raise ValueError("actual and predicted must have the same length.")

    return PerformanceMetrics(
        mae=calculate_mae(actual_values, predicted_values),
        rmse=calculate_rmse(actual_values, predicted_values),
        mape=calculate_mape(actual_values, predicted_values),
        wape=calculate_wape(actual_values, predicted_values),
    )


def calculate_feature_drift(
    reference_features: Mapping[str, Sequence[float]],
    current_features: Mapping[str, Sequence[float]],
    *,
    config: ModelMonitoringConfig = DEFAULT_CONFIG,
) -> list[DriftMetric]:
    """Calculate PSI and KS drift for shared features."""
    reference = validate_feature_mapping(
        reference_features,
        min_size=config.min_sample_size,
    )
    current = validate_feature_mapping(
        current_features,
        min_size=config.min_sample_size,
    )

    shared_features = sorted(set(reference) & set(current))

    if not shared_features:
        raise ValueError(
            "At least one feature must exist in both reference and current data."
        )

    metrics: list[DriftMetric] = []

    for feature_name in shared_features:
        psi_value = calculate_psi(
            reference[feature_name],
            current[feature_name],
        )

        metrics.append(
            DriftMetric(
                metric_name="psi",
                feature_name=feature_name,
                value=psi_value,
                threshold=config.psi_warning_threshold,
                status=classify_psi(
                    psi_value,
                    warning_threshold=config.psi_warning_threshold,
                    critical_threshold=config.psi_critical_threshold,
                ),
            )
        )

        ks_statistic, ks_p_value = calculate_ks(
            reference[feature_name],
            current[feature_name],
        )

        metrics.append(
            DriftMetric(
                metric_name="ks",
                feature_name=feature_name,
                value=ks_statistic,
                threshold=config.ks_significance_level,
                status=classify_ks(
                    ks_p_value,
                    significance_level=config.ks_significance_level,
                ),
            )
        )

    return metrics


def calculate_prediction_drift(
    reference_predictions: Sequence[float],
    current_predictions: Sequence[float],
    *,
    config: ModelMonitoringConfig = DEFAULT_CONFIG,
) -> list[DriftMetric]:
    """Calculate PSI and KS drift for model prediction distributions."""
    reference = validate_numeric_series(
        reference_predictions,
        name="reference_predictions",
        min_size=config.min_sample_size,
    )

    current = validate_numeric_series(
        current_predictions,
        name="current_predictions",
        min_size=config.min_sample_size,
    )

    psi_value = calculate_psi(reference, current)

    psi_metric = DriftMetric(
        metric_name="psi",
        feature_name="__prediction__",
        value=psi_value,
        threshold=config.psi_warning_threshold,
        status=classify_psi(
            psi_value,
            warning_threshold=config.psi_warning_threshold,
            critical_threshold=config.psi_critical_threshold,
        ),
    )

    ks_statistic, ks_p_value = calculate_ks(
        reference,
        current,
    )

    ks_metric = DriftMetric(
        metric_name="ks",
        feature_name="__prediction__",
        value=ks_statistic,
        threshold=config.ks_significance_level,
        status=classify_ks(
            ks_p_value,
            significance_level=config.ks_significance_level,
        ),
    )

    return [psi_metric, ks_metric]


def calculate_performance_degradation(
    reference: PerformanceMetrics,
    current: PerformanceMetrics,
    *,
    threshold: float = DEFAULT_CONFIG.performance_degradation_threshold,
) -> dict[str, float]:
    """Calculate relative degradation for available performance metrics."""
    if threshold < 0:
        raise ValueError("threshold cannot be negative.")

    degradation: dict[str, float] = {}

    metric_names = (
        "mae",
        "rmse",
        "mape",
        "wape",
    )

    for metric_name in metric_names:
        reference_value = getattr(reference, metric_name)
        current_value = getattr(current, metric_name)

        if reference_value is None or current_value is None:
            continue

        if reference_value == 0:
            degradation[metric_name] = (
                0.0 if current_value == 0 else float("inf")
            )
            continue

        degradation[metric_name] = float(
            (current_value - reference_value)
            / abs(reference_value)
        )

    return degradation


def should_retrain(
    drift_metrics: Sequence[DriftMetric],
    performance_degradation: Mapping[str, float],
    *,
    config: ModelMonitoringConfig = DEFAULT_CONFIG,
) -> bool:
    """Determine whether monitoring signals warrant retraining."""
    has_critical_drift = any(
        metric.status == "critical"
        for metric in drift_metrics
    )

    has_performance_degradation = any(
        value >= config.performance_degradation_threshold
        for value in performance_degradation.values()
    )

    return has_critical_drift or has_performance_degradation