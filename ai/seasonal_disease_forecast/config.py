"""Configuration for seasonal disease forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


MODEL_VERSION: Final[str] = "seasonal-disease-forecast-v1"

DEFAULT_FORECAST_HORIZONS: Final[tuple[int, ...]] = (7, 14, 30)

DEFAULT_MIN_HISTORY_POINTS: Final[int] = 30

DEFAULT_LAGS: Final[tuple[int, ...]] = (1, 7, 14, 28)

DEFAULT_ROLLING_WINDOWS: Final[tuple[int, ...]] = (7, 14, 28)

DEFAULT_RANDOM_SEED: Final[int] = 42


@dataclass(frozen=True)
class SeasonalDiseaseForecastConfig:
    """Configuration for seasonal disease forecasting."""

    model_version: str = MODEL_VERSION

    forecast_horizons: tuple[int, ...] = (
        DEFAULT_FORECAST_HORIZONS
    )

    min_history_points: int = (
        DEFAULT_MIN_HISTORY_POINTS
    )

    lags: tuple[int, ...] = DEFAULT_LAGS

    rolling_windows: tuple[int, ...] = (
        DEFAULT_ROLLING_WINDOWS
    )

    random_seed: int = DEFAULT_RANDOM_SEED

    def __post_init__(self) -> None:
        """Validate configuration."""

        if not self.forecast_horizons:
            raise ValueError(
                "forecast_horizons cannot be empty."
            )

        if any(
            horizon <= 0
            for horizon in self.forecast_horizons
        ):
            raise ValueError(
                "Forecast horizons must be positive."
            )

        if self.min_history_points < 2:
            raise ValueError(
                "min_history_points must be at least 2."
            )

        if not self.lags:
            raise ValueError(
                "lags cannot be empty."
            )

        if any(
            lag <= 0
            for lag in self.lags
        ):
            raise ValueError(
                "lags must be positive."
            )

        if not self.rolling_windows:
            raise ValueError(
                "rolling_windows cannot be empty."
            )

        if any(
            window <= 0
            for window in self.rolling_windows
        ):
            raise ValueError(
                "rolling_windows must be positive."
            )


DEFAULT_CONFIG: Final[
    SeasonalDiseaseForecastConfig
] = SeasonalDiseaseForecastConfig()