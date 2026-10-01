"""Configuration for inventory simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


DEFAULT_SHORTAGE_THRESHOLD: Final[float] = 0.0
DEFAULT_LOW_STOCK_THRESHOLD: Final[float] = 0.20
MODEL_VERSION: Final[str] = "inventory-simulation-v1"


@dataclass(frozen=True)
class InventorySimulationConfig:
    """Runtime configuration for inventory simulation."""

    shortage_threshold: float = DEFAULT_SHORTAGE_THRESHOLD
    low_stock_threshold: float = DEFAULT_LOW_STOCK_THRESHOLD
    model_version: str = MODEL_VERSION


DEFAULT_CONFIG: Final[InventorySimulationConfig] = (
    InventorySimulationConfig()
)