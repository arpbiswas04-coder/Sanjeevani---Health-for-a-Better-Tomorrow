"""Configuration for centralized healthcare analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


MODEL_VERSION: Final[str] = "analytics-v1"

DEFAULT_COST_PER_UNIT: Final[float] = 0.0
DEFAULT_WASTAGE_COST_PER_UNIT: Final[float] = 0.0


@dataclass(frozen=True)
class AnalyticsConfig:
    """Configuration for healthcare analytics calculations."""

    model_version: str = MODEL_VERSION
    default_cost_per_unit: float = DEFAULT_COST_PER_UNIT
    default_wastage_cost_per_unit: float = DEFAULT_WASTAGE_COST_PER_UNIT

    def __post_init__(self) -> None:
        """Validate configuration values."""

        if self.default_cost_per_unit < 0.0:
            raise ValueError(
                "Default cost per unit cannot be negative."
            )

        if self.default_wastage_cost_per_unit < 0.0:
            raise ValueError(
                "Default wastage cost per unit cannot be negative."
            )


DEFAULT_CONFIG: Final[AnalyticsConfig] = AnalyticsConfig()