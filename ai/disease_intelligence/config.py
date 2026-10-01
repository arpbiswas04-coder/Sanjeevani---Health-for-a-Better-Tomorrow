"""Configuration for disease intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


DEFAULT_MIN_HISTORY_POINTS: Final[int] = 14
DEFAULT_GROWTH_WINDOW: Final[int] = 7
DEFAULT_Z_THRESHOLD: Final[float] = 2.0
DEFAULT_HIGH_SURGE_PROBABILITY: Final[float] = 0.70
DEFAULT_CRITICAL_SURGE_PROBABILITY: Final[float] = 0.90
DEFAULT_RANDOM_SEED: Final[int] = 42


@dataclass(frozen=True)
class DiseaseIntelligenceConfig:
    """Runtime configuration for outbreak early warning."""

    min_history_points: int = DEFAULT_MIN_HISTORY_POINTS
    growth_window: int = DEFAULT_GROWTH_WINDOW
    z_threshold: float = DEFAULT_Z_THRESHOLD
    high_surge_probability: float = (
        DEFAULT_HIGH_SURGE_PROBABILITY
    )
    critical_surge_probability: float = (
        DEFAULT_CRITICAL_SURGE_PROBABILITY
    )
    random_seed: int = DEFAULT_RANDOM_SEED


DEFAULT_CONFIG: Final[DiseaseIntelligenceConfig] = (
    DiseaseIntelligenceConfig()
)