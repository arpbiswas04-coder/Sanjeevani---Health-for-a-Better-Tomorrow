"""Tests for model performance and drift monitoring."""

from __future__ import annotations

import numpy as np
import pytest

from ai.model_monitoring.evaluate import (
    calculate_feature_drift,
    calculate_performance_degradation,
    calculate_performance_metrics,
    calculate_prediction_drift,
    should_retrain,
)
from ai.model_monitoring.predict import ModelMonitoringPredictor, monitor_model
from ai.model_monitoring.schema import PerformanceMetrics
from ai.model_monitoring.train import train_monitoring_baseline


def stable_series(size: int = 30) -> list[float]:
    """Create deterministic reference data."""
    return [float(index) for index in range(size)]


def shifted_series(size: int = 30, shift: float = 100.0) -> list[float]:
    """Create deterministic shifted data."""
    return [float(index) + shift for index in range(size)]


def test_performance_metrics_are_calculated() -> None:
    actual = [10.0, 20.0, 30.0]
    predicted = [11.0, 18.0, 33.0]

    result = calculate_performance_metrics(actual, predicted)

    assert result.mae is not None
    assert result.rmse is not None
    assert result.mape is not None
    assert result.wape is not None


def test_performance_metrics_reject_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        calculate_performance_metrics(
            [1.0, 2.0],
            [1.0],
        )


def test_feature_drift_is_stable_for_identical_data() -> None:
    values = stable_series()

    metrics = calculate_feature_drift(
        {"feature_a": values},
        {"feature_a": values},
    )

    assert len(metrics) == 2
    assert all(metric.status == "stable" for metric in metrics)


def test_feature_drift_detects_shifted_distribution() -> None:
    metrics = calculate_feature_drift(
        {"feature_a": stable_series()},
        {"feature_a": shifted_series()},
    )

    assert any(metric.status in {"warning", "critical"} for metric in metrics)


def test_prediction_drift_is_stable_for_identical_predictions() -> None:
    values = stable_series()

    metrics = calculate_prediction_drift(
        values,
        values,
    )

    assert len(metrics) == 2
    assert all(metric.status == "stable" for metric in metrics)


def test_prediction_drift_detects_shift() -> None:
    metrics = calculate_prediction_drift(
        stable_series(),
        shifted_series(),
    )

    assert any(metric.status in {"warning", "critical"} for metric in metrics)


def test_performance_degradation_detects_increased_error() -> None:
    reference = PerformanceMetrics(
        mae=10.0,
        rmse=12.0,
        mape=10.0,
        wape=10.0,
    )

    current = PerformanceMetrics(
        mae=15.0,
        rmse=18.0,
        mape=15.0,
        wape=15.0,
    )

    degradation = calculate_performance_degradation(
        reference,
        current,
    )

    assert degradation["mae"] == pytest.approx(0.5)
    assert degradation["rmse"] == pytest.approx(0.5)


def test_performance_improvement_is_not_degradation() -> None:
    reference = PerformanceMetrics(mae=10.0)
    current = PerformanceMetrics(mae=8.0)

    degradation = calculate_performance_degradation(
        reference,
        current,
    )

    assert degradation["mae"] == pytest.approx(-0.2)


def test_should_retrain_on_critical_drift() -> None:
    metrics = calculate_prediction_drift(
        stable_series(),
        shifted_series(),
    )

    assert should_retrain(
        metrics,
        {},
    )


def test_should_retrain_on_performance_degradation() -> None:
    reference = PerformanceMetrics(mae=10.0)
    current = PerformanceMetrics(mae=13.0)

    degradation = calculate_performance_degradation(
        reference,
        current,
    )

    assert should_retrain(
        [],
        degradation,
    )


def test_should_not_retrain_when_stable() -> None:
    metrics = calculate_prediction_drift(
        stable_series(),
        stable_series(),
    )

    assert not should_retrain(
        metrics,
        {"mae": 0.05},
    )


def test_monitoring_baseline_requires_enough_samples() -> None:
    with pytest.raises(ValueError):
        train_monitoring_baseline(
            reference_features={"feature_a": [1.0, 2.0]},
            reference_predictions=[1.0, 2.0],
        )


def test_monitoring_baseline_is_created() -> None:
    values = stable_series()

    baseline = train_monitoring_baseline(
        reference_features={"feature_a": values},
        reference_predictions=values,
    )

    assert "feature_a" in baseline.reference_features
    assert len(baseline.reference_predictions) == 30


def test_predictor_requires_fitted_baseline() -> None:
    predictor = ModelMonitoringPredictor()

    with pytest.raises(RuntimeError):
        predictor.predict(
            {
                "model_name": "test-model",
                "model_version": "v1",
                "reference_features": {"feature_a": stable_series()},
                "current_features": {"feature_a": stable_series()},
                "reference_predictions": stable_series(),
                "current_predictions": stable_series(),
            }
        )


def test_predictor_returns_monitoring_response() -> None:
    values = stable_series()

    predictor = ModelMonitoringPredictor()

    predictor.fit(
        reference_features={"feature_a": values},
        reference_predictions=values,
    )

    result = predictor.predict(
        {
            "model_name": "test-model",
            "model_version": "v1",
            "reference_features": {"feature_a": values},
            "current_features": {"feature_a": values},
            "reference_predictions": values,
            "current_predictions": values,
        }
    )

    assert result["success"] is True
    assert result["model_name"] == "test-model"
    assert result["model_version"] == "v1"
    assert result["overall_status"] == "stable"
    assert result["retraining_recommended"] is False
    assert len(result["drift_metrics"]) == 4


def test_predictor_detects_prediction_drift() -> None:
    reference = stable_series()
    current = shifted_series()

    predictor = ModelMonitoringPredictor()

    predictor.fit(
        reference_features={"feature_a": reference},
        reference_predictions=reference,
    )

    result = predictor.predict(
        {
            "model_name": "test-model",
            "model_version": "v1",
            "reference_features": {"feature_a": reference},
            "current_features": {"feature_a": reference},
            "reference_predictions": reference,
            "current_predictions": current,
        }
    )

    prediction_metrics = [
        metric
        for metric in result["drift_metrics"]
        if metric["feature_name"] == "__prediction__"
    ]

    assert len(prediction_metrics) == 2
    assert any(
        metric["status"] in {"warning", "critical"}
        for metric in prediction_metrics
    )


def test_monitor_model_convenience_function() -> None:
    values = stable_series()

    result = monitor_model(
        reference_features={"feature_a": values},
        current_features={"feature_a": values},
        reference_predictions=values,
        current_predictions=values,
        model_name="test-model",
        model_version="v1",
    )

    assert result["success"] is True
    assert result["overall_status"] == "stable"


def test_monitor_model_detects_performance_degradation() -> None:
    values = stable_series()

    reference_performance = PerformanceMetrics(
        mae=10.0,
        rmse=10.0,
        mape=10.0,
        wape=10.0,
    )

    current_performance = PerformanceMetrics(
        mae=13.0,
        rmse=10.0,
        mape=10.0,
        wape=10.0,
    )

    result = monitor_model(
        reference_features={"feature_a": values},
        current_features={"feature_a": values},
        reference_predictions=values,
        current_predictions=values,
        model_name="test-model",
        model_version="v1",
        reference_performance=reference_performance,
        current_performance=current_performance,
    )

    assert result["retraining_recommended"] is True
    assert result["performance_degradation"]["mae"] == pytest.approx(0.3)


def test_non_finite_data_is_rejected() -> None:
    values = stable_series()

    with pytest.raises(ValueError):
        calculate_prediction_drift(
            values,
            values[:-1] + [float("nan")],
        )


def test_numpy_values_are_supported() -> None:
    values = np.arange(30, dtype=float)

    metrics = calculate_prediction_drift(
        values,
        values,
    )

    assert len(metrics) == 2
    assert all(metric.status == "stable" for metric in metrics)