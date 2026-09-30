"""Configuration for composite healthcare resilience risk scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


MODEL_VERSION: Final[str] = "risk-scoring-v1"

# Implementation defaults because the repository does not document weights.
DEFAULT_WEIGHTS: Final[dict[str, float]] = {
    "supply_risk": 0.25,
    "bed_risk": 0.25,
    "workforce_risk": 0.20,
    "disease_risk": 0.20,
    "anomaly_risk": 0.10,
}

# Normalized risk thresholds.
LOW_MAX: Final[float] = 0.25
MODERATE_MAX: Final[float] = 0.50
HIGH_MAX: Final[float] = 0.75


@dataclass(frozen=True)
class RiskScoringConfig:
    """Configuration for deterministic composite resilience scoring."""

    weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_WEIGHTS)
    )
    low_max: float = LOW_MAX
    moderate_max: float = MODERATE_MAX
    high_max: float = HIGH_MAX
    model_version: str = MODEL_VERSION


DEFAULT_CONFIG: Final[RiskScoringConfig] = RiskScoringConfig()