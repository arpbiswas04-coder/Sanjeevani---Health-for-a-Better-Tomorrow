"""Configuration for predictive procurement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


DEFAULT_FORECAST_HORIZON_DAYS: Final[int] = 7
DEFAULT_MIN_HISTORY_POINTS: Final[int] = 7
DEFAULT_LOOKBACK_DAYS: Final[int] = 14
DEFAULT_SAFETY_STOCK_DAYS: Final[float] = 2.0
DEFAULT_SHORTAGE_THRESHOLD: Final[float] = 0.0
DEFAULT_RANDOM_SEED: Final[int] = 42
MODEL_VERSION: Final[str] = "predictive-procurement-v1"


@dataclass(frozen=True)
class PredictiveProcurementConfig:
    """Runtime configuration for procurement prediction."""

    forecast_horizon_days: int = DEFAULT_FORECAST_HORIZON_DAYS
    min_history_points: int = DEFAULT_MIN_HISTORY_POINTS
    lookback_days: int = DEFAULT_LOOKBACK_DAYS
    safety_stock_days: float = DEFAULT_SAFETY_STOCK_DAYS
    shortage_threshold: float = DEFAULT_SHORTAGE_THRESHOLD
    random_seed: int = DEFAULT_RANDOM_SEED
    model_version: str = MODEL_VERSION


DEFAULT_CONFIG: Final[PredictiveProcurementConfig] = (
    PredictiveProcurementConfig()
)