"""Configuration for bed occupancy forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


# Required forecasting horizons from the project specification:
# 24 hours, 48 hours, and 7 days.
DEFAULT_FORECAST_HORIZONS: Final[tuple[int, ...]] = (1, 2, 7)

# Occupancy saturation thresholds specified by the project.
SATURATION_WARNING_THRESHOLD: Final[float] = 0.85
SATURATION_CRITICAL_THRESHOLD: Final[float] = 0.95

# Implementation defaults for time-series feature generation.
DEFAULT_MIN_HISTORY_POINTS: Final[int] = 14
DEFAULT_LAGS: Final[tuple[int, ...]] = (1, 2, 7)
DEFAULT_ROLLING_WINDOWS: Final[tuple[int, ...]] = (2, 7)

DEFAULT_RANDOM_SEED: Final[int] = 42


@dataclass(frozen=True)
class BedForecastConfig:
    """Configuration used by the bed occupancy forecasting pipeline."""

    forecast_horizons: tuple[int, ...] = DEFAULT_FORECAST_HORIZONS

    # Minimum historical observations required by the forecasting pipeline.
    min_history_points: int = DEFAULT_MIN_HISTORY_POINTS

    # Historical occupancy lags used as model features.
    lags: tuple[int, ...] = DEFAULT_LAGS

    # Shifted rolling windows used to avoid future-data leakage.
    rolling_windows: tuple[int, ...] = DEFAULT_ROLLING_WINDOWS

    # Occupancy thresholds for operational saturation warnings.
    saturation_warning_threshold: float = SATURATION_WARNING_THRESHOLD
    saturation_critical_threshold: float = SATURATION_CRITICAL_THRESHOLD

    random_seed: int = DEFAULT_RANDOM_SEED


DEFAULT_CONFIG: Final[BedForecastConfig] = BedForecastConfig()