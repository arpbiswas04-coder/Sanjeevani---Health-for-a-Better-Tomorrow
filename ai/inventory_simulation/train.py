"""Model interface for inventory simulation."""

from __future__ import annotations

from dataclasses import dataclass

from .config import (
    DEFAULT_CONFIG,
    InventorySimulationConfig,
)


@dataclass(frozen=True)
class InventorySimulationModel:
    """Deterministic inventory simulation model."""

    model_version: str


def train_model(
    *,
    config: InventorySimulationConfig = DEFAULT_CONFIG,
) -> InventorySimulationModel:
    """Create the deterministic simulation model."""

    return InventorySimulationModel(
        model_version=config.model_version,
    )