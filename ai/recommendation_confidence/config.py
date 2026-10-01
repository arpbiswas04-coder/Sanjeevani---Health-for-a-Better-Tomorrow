"""Configuration for recommendation confidence scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


MODEL_VERSION: Final[str] = "recommendation-confidence-v1"

# Default weights for the three evidence sources.
# These are implementation defaults, not externally defined standards.
VALIDATION_WEIGHT: Final[float] = 0.50
INTERVAL_WEIGHT: Final[float] = 0.30
CALIBRATION_WEIGHT: Final[float] = 0.20

# Confidence-level boundaries.
HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.80
MODERATE_CONFIDENCE_THRESHOLD: Final[float] = 0.60

# Default target prediction-interval coverage.
DEFAULT_TARGET_INTERVAL_COVERAGE: Final[float] = 0.95

# Calibration-error thresholds.
EXCELLENT_CALIBRATION_ERROR: Final[float] = 0.05
POOR_CALIBRATION_ERROR: Final[float] = 0.20


@dataclass(frozen=True)
class RecommendationConfidenceConfig:
    """Configuration for transparent recommendation confidence scoring."""

    validation_weight: float = VALIDATION_WEIGHT
    interval_weight: float = INTERVAL_WEIGHT
    calibration_weight: float = CALIBRATION_WEIGHT

    high_confidence_threshold: float = HIGH_CONFIDENCE_THRESHOLD
    moderate_confidence_threshold: float = MODERATE_CONFIDENCE_THRESHOLD

    target_interval_coverage: float = DEFAULT_TARGET_INTERVAL_COVERAGE

    excellent_calibration_error: float = EXCELLENT_CALIBRATION_ERROR
    poor_calibration_error: float = POOR_CALIBRATION_ERROR

    model_version: str = MODEL_VERSION

    def __post_init__(self) -> None:
        """Validate configuration values."""

        weights = (
            self.validation_weight,
            self.interval_weight,
            self.calibration_weight,
        )

        if any(weight < 0.0 for weight in weights):
            raise ValueError("Confidence weights cannot be negative.")

        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("Confidence weights must sum to 1.0.")

        if not 0.0 < self.moderate_confidence_threshold <= 1.0:
            raise ValueError(
                "Moderate confidence threshold must be in (0, 1]."
            )

        if not (
            self.moderate_confidence_threshold
            < self.high_confidence_threshold
            <= 1.0
        ):
            raise ValueError(
                "High confidence threshold must be greater than "
                "moderate threshold and at most 1."
            )

        if not 0.0 < self.target_interval_coverage <= 1.0:
            raise ValueError(
                "Target interval coverage must be in (0, 1]."
            )

        if self.excellent_calibration_error < 0.0:
            raise ValueError(
                "Excellent calibration error cannot be negative."
            )

        if self.poor_calibration_error < self.excellent_calibration_error:
            raise ValueError(
                "Poor calibration error must be greater than or equal "
                "to excellent calibration error."
            )


DEFAULT_CONFIG: Final[RecommendationConfidenceConfig] = (
    RecommendationConfidenceConfig()
)