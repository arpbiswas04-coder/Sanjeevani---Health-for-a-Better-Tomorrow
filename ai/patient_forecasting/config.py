"""Configuration for patient footfall forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


# Forecast horizons required by the Member 3 specification:
# next day and next 7 days.
DEFAULT_FORECAST_HORIZONS: Final[tuple[int, ...]] = (1, 7)

# Implementation default.
# The source specification does not define a minimum history size.
DEFAULT_MIN_HISTORY_POINTS: Final[int] = 14

# Time-series lag features.
DEFAULT_LAGS: Final[tuple[int, ...]] = (1, 7, 14)

# Rolling-window features.
DEFAULT_ROLLING_WINDOWS: Final[tuple[int, ...]] = (7, 14)

# Keeps model behavior deterministic.
DEFAULT_RANDOM_SEED: Final[int] = 42


@dataclass(frozen=True)
class PatientForecastConfig:
    """Runtime configuration for patient footfall forecasting."""

    forecast_horizons: tuple[int, ...] = DEFAULT_FORECAST_HORIZONS
    min_history_points: int = DEFAULT_MIN_HISTORY_POINTS
    lags: tuple[int, ...] = DEFAULT_LAGS
    rolling_windows: tuple[int, ...] = DEFAULT_ROLLING_WINDOWS
    random_seed: int = DEFAULT_RANDOM_SEED


DEFAULT_CONFIG: Final[PatientForecastConfig] = PatientForecastConfig()