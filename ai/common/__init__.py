"""
Sanjeevani Grid - Common AI Foundation Package
ai/common/__init__.py

Exports core base abstractions, canonical risk levels, validation helpers,
evaluation metrics, and artifact serialization.
"""

from ai.common.base_model import BaseForecaster, BasePredictor, BaseScorer
from ai.common.metrics import (
    calculate_brier_score,
    calculate_classification_metrics,
    calculate_forecasting_metrics,
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    calculate_wape,
)
from ai.common.serialization import load_artifact, save_artifact
from ai.common.tracking import TrackingRunResult, is_mlflow_available, track_training
from ai.common.types import (
    RiskLevel,
    ensure_utc_iso8601,
    ensure_uuid_v4,
    format_utc_iso8601,
    is_valid_utc_iso8601,
    is_valid_uuid_v4,
    now_utc_iso8601,
)

__all__ = [
    "BaseForecaster",
    "BasePredictor",
    "BaseScorer",
    "RiskLevel",
    "is_valid_uuid_v4",
    "ensure_uuid_v4",
    "is_valid_utc_iso8601",
    "ensure_utc_iso8601",
    "format_utc_iso8601",
    "now_utc_iso8601",
    "calculate_mae",
    "calculate_rmse",
    "calculate_mape",
    "calculate_wape",
    "calculate_forecasting_metrics",
    "calculate_brier_score",
    "calculate_classification_metrics",
    "save_artifact",
    "load_artifact",
    "track_training",
    "is_mlflow_available",
    "TrackingRunResult",
]
