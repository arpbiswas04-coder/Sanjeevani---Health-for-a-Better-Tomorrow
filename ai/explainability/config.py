"""Configuration for model explainability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


MODEL_VERSION: Final[str] = "explainability-v1"
DEFAULT_TOP_K: Final[int] = 5


@dataclass(frozen=True)
class ExplainabilityConfig:
    """Configuration for deterministic feature attribution."""

    top_k: int = DEFAULT_TOP_K
    model_version: str = MODEL_VERSION


DEFAULT_CONFIG: Final[ExplainabilityConfig] = ExplainabilityConfig()