"""
Sanjeevani Grid - MLflow Tracking Utilities
ai/common/tracking.py

Provides unified experiment tracking, parameter/metric logging, and native XGBoost
model artifact logging. Designed to operate seamlessly with local or remote tracking
servers and gracefully fall back when MLflow is not installed in the environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import os
from typing import Any, Mapping, Optional

from ai.common.types import now_utc_iso8601

logger = logging.getLogger(__name__)

try:
    import mlflow
    import mlflow.xgboost
    _HAS_MLFLOW = True
except ImportError:
    mlflow = None  # type: ignore[assignment]
    _HAS_MLFLOW = False


@dataclass
class TrackingRunResult:
    """Structured result from an MLflow tracking invocation."""

    run_id: Optional[str]
    experiment_name: str
    model_name: str
    model_version: str
    status: str  # "logged", "fallback", "disabled", "error"
    params: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    is_fallback: bool = False
    error: Optional[str] = None


def is_mlflow_available() -> bool:
    """Check if the MLflow package is installed and importable."""
    return _HAS_MLFLOW


def is_tracking_enabled() -> bool:
    """Determine if tracking is globally enabled via environment variables."""
    disabled = os.getenv("SANJEEVANI_DISABLE_MLFLOW", "0").strip().lower()
    return disabled not in ("1", "true", "yes")


def get_default_tracking_uri() -> str:
    """Return configured tracking URI or standard local file-based repository."""
    return os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")


def sanitize_params(params: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    """Sanitize parameters to scalar types accepted by MLflow."""
    if not params:
        return {}
    clean: dict[str, Any] = {}
    for k, v in params.items():
        if isinstance(v, (int, float, str, bool)):
            clean[str(k)] = v
        elif isinstance(v, (list, tuple, set)):
            clean[str(k)] = str(list(v))[:250]
        elif v is None:
            clean[str(k)] = "None"
        else:
            clean[str(k)] = str(v)[:250]
    return clean


def sanitize_metrics(metrics: Optional[Mapping[str, Any]]) -> dict[str, float]:
    """Sanitize metric values ensuring they are finite float values."""
    if not metrics:
        return {}
    clean: dict[str, float] = {}
    for k, v in metrics.items():
        try:
            val = float(v)
            if val == val and val not in (float("inf"), float("-inf")):
                clean[str(k)] = val
        except (ValueError, TypeError):
            continue
    return clean


def track_training(
    *,
    model_name: str,
    model_version: str,
    params: Optional[Mapping[str, Any]] = None,
    metrics: Optional[Mapping[str, Any]] = None,
    booster: Optional[Any] = None,
    dataset_info: Optional[Mapping[str, Any]] = None,
    tags: Optional[Mapping[str, str]] = None,
    experiment_name: str = "sanjeevani-ai",
    tracking_uri: Optional[str] = None,
) -> TrackingRunResult:
    """
    Log training run parameters, metrics, tags, and native XGBoost Booster to MLflow.

    Features:
    - Sets or reuses configured experiment name
    - Logs training timestamp and model metadata tags
    - Logs native XGBoost booster with `mlflow.xgboost.log_model` (never mlflow.sklearn)
    - Gracefully falls back when MLflow is not installed or disabled, preserving execution
    """
    clean_params = sanitize_params(params)
    clean_metrics = sanitize_metrics(metrics)

    if not is_tracking_enabled():
        return TrackingRunResult(
            run_id=None,
            experiment_name=experiment_name,
            model_name=model_name,
            model_version=model_version,
            status="disabled",
            params=clean_params,
            metrics=clean_metrics,
            is_fallback=True,
        )

    if not _HAS_MLFLOW:
        logger.debug(
            "MLflow is not installed in the environment. Tracking executed in fallback mode for %s.",
            model_name,
        )
        return TrackingRunResult(
            run_id=None,
            experiment_name=experiment_name,
            model_name=model_name,
            model_version=model_version,
            status="fallback",
            params=clean_params,
            metrics=clean_metrics,
            is_fallback=True,
        )

    try:
        active_uri = tracking_uri or get_default_tracking_uri()
        mlflow.set_tracking_uri(active_uri)
        mlflow.set_experiment(experiment_name)

        run_name = f"{model_name}-{model_version}"
        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id

            # Standard metadata tags
            mlflow.set_tag("model_name", model_name)
            mlflow.set_tag("model_version", model_version)
            mlflow.set_tag("training_timestamp", now_utc_iso8601())

            if tags:
                for tag_k, tag_v in tags.items():
                    mlflow.set_tag(str(tag_k), str(tag_v))

            if dataset_info:
                for dk, dv in dataset_info.items():
                    mlflow.set_tag(f"dataset.{dk}", str(dv))

            if clean_params:
                mlflow.log_params(clean_params)

            if clean_metrics:
                mlflow.log_metrics(clean_metrics)

            # Native XGBoost Booster logging
            if booster is not None:
                mlflow.xgboost.log_model(
                    booster,
                    artifact_path="model",
                )

            return TrackingRunResult(
                run_id=run_id,
                experiment_name=experiment_name,
                model_name=model_name,
                model_version=model_version,
                status="logged",
                params=clean_params,
                metrics=clean_metrics,
                is_fallback=False,
            )

    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "MLflow tracking encountered an error during %s training: %s",
            model_name,
            exc,
        )
        return TrackingRunResult(
            run_id=None,
            experiment_name=experiment_name,
            model_name=model_name,
            model_version=model_version,
            status="error",
            params=clean_params,
            metrics=clean_metrics,
            is_fallback=True,
            error=str(exc),
        )
