"""Configuration for model performance and drift monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


MODEL_VERSION: Final[str] = "model-monitoring-v1"

# PSI interpretation thresholds.
PSI_WARNING_THRESHOLD: Final[float] = 0.10
PSI_CRITICAL_THRESHOLD: Final[float] = 0.25

# KS two-sample test significance level.
KS_SIGNIFICANCE_LEVEL: Final[float] = 0.05

# Relative performance degradation threshold.
PERFORMANCE_DEGRADATION_THRESHOLD: Final[float] = 0.20

# Minimum samples required for reliable distribution comparison.
MIN_SAMPLE_SIZE: Final[int] = 20


@dataclass(frozen=True)
class ModelMonitoringConfig:
    """Configuration for model monitoring."""

    psi_warning_threshold: float = PSI_WARNING_THRESHOLD
    psi_critical_threshold: float = PSI_CRITICAL_THRESHOLD
    ks_significance_level: float = KS_SIGNIFICANCE_LEVEL
    performance_degradation_threshold: float = PERFORMANCE_DEGRADATION_THRESHOLD
    min_sample_size: int = MIN_SAMPLE_SIZE
    model_version: str = MODEL_VERSION


DEFAULT_CONFIG: Final[ModelMonitoringConfig] = ModelMonitoringConfig()