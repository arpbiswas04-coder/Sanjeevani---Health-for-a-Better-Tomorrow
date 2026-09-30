"""Configuration for workforce forecasting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


DEFAULT_FORECAST_HORIZONS: Final[tuple[int, ...]] = (1, 7)

DEFAULT_MIN_HISTORY_POINTS: Final[int] = 14

DEFAULT_RANDOM_SEED: Final[int] = 42

# Implementation defaults.
# The project requirements specify staff-to-patient rules,
# while the numeric ratios remain configurable.
DEFAULT_STAFF_TO_PATIENT_RATIOS: Final[dict[str, float]] = {
    "doctor": 10.0,
    "nurse": 4.0,
    "support": 8.0,
}


@dataclass(frozen=True)
class WorkforceForecastConfig:
    """Configuration used by the workforce forecaster."""

    forecast_horizons: tuple[int, ...] = (
        DEFAULT_FORECAST_HORIZONS
    )

    min_history_points: int = (
        DEFAULT_MIN_HISTORY_POINTS
    )

    staff_to_patient_ratios: dict[str, float] = field(
        default_factory=lambda: dict(
            DEFAULT_STAFF_TO_PATIENT_RATIOS
        )
    )

    random_seed: int = DEFAULT_RANDOM_SEED


DEFAULT_CONFIG: Final[WorkforceForecastConfig] = (
    WorkforceForecastConfig()
)