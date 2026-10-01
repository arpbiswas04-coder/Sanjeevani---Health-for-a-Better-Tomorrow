"""Unit tests for MLflow tracking utility and native XGBoost logging."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

from ai.common.tracking import (
    TrackingRunResult,
    get_default_tracking_uri,
    is_mlflow_available,
    is_tracking_enabled,
    sanitize_metrics,
    sanitize_params,
    track_training,
)


def test_is_mlflow_available_returns_bool() -> None:
    available = is_mlflow_available()
    assert isinstance(available, bool)


def test_is_tracking_enabled_respects_env() -> None:
    original = os.environ.get("SANJEEVANI_DISABLE_MLFLOW")
    try:
        os.environ["SANJEEVANI_DISABLE_MLFLOW"] = "1"
        assert is_tracking_enabled() is False

        os.environ["SANJEEVANI_DISABLE_MLFLOW"] = "true"
        assert is_tracking_enabled() is False

        os.environ["SANJEEVANI_DISABLE_MLFLOW"] = "0"
        assert is_tracking_enabled() is True
    finally:
        if original is not None:
            os.environ["SANJEEVANI_DISABLE_MLFLOW"] = original
        else:
            os.environ.pop("SANJEEVANI_DISABLE_MLFLOW", None)


def test_get_default_tracking_uri() -> None:
    original = os.environ.get("MLFLOW_TRACKING_URI")
    try:
        os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
        assert get_default_tracking_uri() == "http://localhost:5000"

        os.environ.pop("MLFLOW_TRACKING_URI", None)
        assert get_default_tracking_uri() == "file:./mlruns"
    finally:
        if original is not None:
            os.environ["MLFLOW_TRACKING_URI"] = original
        else:
            os.environ.pop("MLFLOW_TRACKING_URI", None)


def test_sanitize_params() -> None:
    params = {
        "lr": 0.05,
        "max_depth": 4,
        "features": ["f1", "f2"],
        "none_val": None,
    }
    clean = sanitize_params(params)
    assert clean["lr"] == 0.05
    assert clean["max_depth"] == 4
    assert clean["none_val"] == "None"
    assert "f1" in clean["features"]
    assert sanitize_params(None) == {}


def test_sanitize_metrics() -> None:
    metrics = {
        "rmse": 1.25,
        "nan_metric": float("nan"),
        "inf_metric": float("inf"),
        "invalid": "not-a-number",
    }
    clean = sanitize_metrics(metrics)
    assert clean == {"rmse": 1.25}
    assert sanitize_metrics(None) == {}


def test_track_training_disabled_by_env() -> None:
    with patch.dict(os.environ, {"SANJEEVANI_DISABLE_MLFLOW": "1"}):
        result = track_training(
            model_name="TestModel",
            model_version="v1",
            params={"depth": 3},
            metrics={"rmse": 0.5},
        )
        assert result.status == "disabled"
        assert result.is_fallback is True
        assert result.run_id is None
        assert result.params == {"depth": 3}
        assert result.metrics == {"rmse": 0.5}


def test_track_training_fallback_without_mlflow() -> None:
    with patch("ai.common.tracking._HAS_MLFLOW", False):
        result = track_training(
            model_name="FallbackModel",
            model_version="v1",
            params={"max_depth": 5},
            metrics={"mae": 2.1},
        )
        assert result.status == "fallback"
        assert result.is_fallback is True
        assert result.run_id is None
        assert result.model_name == "FallbackModel"
        assert result.params == {"max_depth": 5}
        assert result.metrics == {"mae": 2.1}


def test_track_training_with_active_mlflow() -> None:
    mock_mlflow = MagicMock()
    mock_run = MagicMock()
    mock_run.info.run_id = "test-run-12345"
    mock_mlflow.start_run.return_value.__enter__.return_value = mock_run

    mock_booster = MagicMock()

    with patch("ai.common.tracking._HAS_MLFLOW", True), \
         patch("ai.common.tracking.mlflow", mock_mlflow):

        result = track_training(
            model_name="XGBoostDemandForecaster",
            model_version="demand-v1",
            params={"learning_rate": 0.05, "max_depth": 4},
            metrics={"mae": 1.5, "rmse": 2.0},
            booster=mock_booster,
            dataset_info={"samples": 120, "split": "chronological"},
            tags={"domain": "pharmacy"},
            experiment_name="test-demand-experiment",
        )

        assert result.status == "logged"
        assert result.is_fallback is False
        assert result.run_id == "test-run-12345"

        mock_mlflow.set_experiment.assert_called_with("test-demand-experiment")
        mock_mlflow.log_params.assert_called_once_with({"learning_rate": 0.05, "max_depth": 4})
        mock_mlflow.log_metrics.assert_called_once_with({"mae": 1.5, "rmse": 2.0})

        # Verify native XGBoost logging is invoked (never sklearn)
        mock_mlflow.xgboost.log_model.assert_called_once_with(
            mock_booster,
            artifact_path="model",
        )


def test_track_training_handles_exception_gracefully() -> None:
    mock_mlflow = MagicMock()
    mock_mlflow.set_experiment.side_effect = RuntimeError("Connection to tracking server refused")

    with patch("ai.common.tracking._HAS_MLFLOW", True), \
         patch("ai.common.tracking.mlflow", mock_mlflow):

        result = track_training(
            model_name="ErrorModel",
            model_version="v1",
            params={},
            metrics={},
        )

        assert result.status == "error"
        assert result.is_fallback is True
        assert "Connection to tracking server refused" in str(result.error)
