"""Core confidence-scoring calculations."""

from __future__ import annotations

from .config import DEFAULT_CONFIG, RecommendationConfidenceConfig
from .schema import ConfidenceLevel


def _clamp(value: float) -> float:
    """Clamp a numeric value to the [0, 1] range."""
    return max(0.0, min(1.0, float(value)))


def calculate_interval_evidence(
    interval_coverage: float,
    target_interval_coverage: float,
) -> float:
    """Convert interval coverage into an evidence score.

    Coverage at or above the target receives full evidence.
    Lower coverage is scaled proportionally to the target.

    This is an evidence score, not a statistical probability.
    """
    if not 0.0 <= interval_coverage <= 1.0:
        raise ValueError("Interval coverage must be between 0 and 1.")

    if not 0.0 < target_interval_coverage <= 1.0:
        raise ValueError(
            "Target interval coverage must be greater than 0 and at most 1."
        )

    return _clamp(interval_coverage / target_interval_coverage)


def calculate_calibration_evidence(
    calibration_error: float,
    *,
    excellent_error: float = DEFAULT_CONFIG.excellent_calibration_error,
    poor_error: float = DEFAULT_CONFIG.poor_calibration_error,
) -> float:
    """Convert calibration error into an evidence score.

    Zero calibration error receives full evidence.
    Calibration error at or above the configured poor threshold
    receives zero evidence.
    """
    if calibration_error < 0.0:
        raise ValueError("Calibration error cannot be negative.")

    if excellent_error < 0.0:
        raise ValueError(
            "Excellent calibration error cannot be negative."
        )

    if poor_error < excellent_error:
        raise ValueError(
            "Poor calibration error must be greater than or equal "
            "to excellent calibration error."
        )

    if calibration_error <= excellent_error:
        return 1.0

    if calibration_error >= poor_error:
        return 0.0

    span = poor_error - excellent_error

    return _clamp(
        1.0 - ((calibration_error - excellent_error) / span)
    )


def calculate_confidence_score(
    validation_score: float,
    interval_coverage: float,
    calibration_error: float,
    *,
    target_interval_coverage: float = DEFAULT_CONFIG.target_interval_coverage,
    config: RecommendationConfidenceConfig = DEFAULT_CONFIG,
) -> float:
    """Calculate a transparent confidence evidence score.

    The result combines:
    - validation performance,
    - prediction-interval coverage,
    - calibration quality.

    The returned value is an evidence score in [0, 1].
    It must not be interpreted as the probability that a
    recommendation is correct.
    """
    if not 0.0 <= validation_score <= 1.0:
        raise ValueError("Validation score must be between 0 and 1.")

    interval_evidence = calculate_interval_evidence(
        interval_coverage,
        target_interval_coverage,
    )

    calibration_evidence = calculate_calibration_evidence(
        calibration_error,
        excellent_error=config.excellent_calibration_error,
        poor_error=config.poor_calibration_error,
    )

    score = (
        config.validation_weight * validation_score
        + config.interval_weight * interval_evidence
        + config.calibration_weight * calibration_evidence
    )

    return _clamp(score)


def classify_confidence(
    confidence_score: float,
    *,
    config: RecommendationConfidenceConfig = DEFAULT_CONFIG,
) -> ConfidenceLevel:
    """Map a confidence evidence score to a confidence level."""
    if not 0.0 <= confidence_score <= 1.0:
        raise ValueError(
            "Confidence score must be between 0 and 1."
        )

    if confidence_score >= config.high_confidence_threshold:
        return "high"

    if confidence_score >= config.moderate_confidence_threshold:
        return "moderate"

    return "low"