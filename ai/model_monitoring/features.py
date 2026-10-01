"""Feature-level drift calculations for model monitoring."""

from __future__ import annotations

from math import log
from typing import Iterable

import numpy as np
from scipy.stats import ks_2samp


def _validate_values(values: Iterable[float]) -> np.ndarray:
    """Convert values to a finite one-dimensional NumPy array."""
    array = np.asarray(list(values), dtype=float)

    if array.ndim != 1:
        raise ValueError("Values must be one-dimensional.")

    if array.size == 0:
        raise ValueError("Values cannot be empty.")

    if not np.all(np.isfinite(array)):
        raise ValueError("Values must contain only finite numbers.")

    return array


def calculate_psi(
    reference: Iterable[float],
    current: Iterable[float],
    bins: int = 10,
) -> float:
    """Calculate Population Stability Index (PSI).

    PSI compares the distribution of current observations with a
    reference distribution.

    Values:
        < 0.10: generally treated as stable by this implementation.
        0.10-0.25: warning range.
        > 0.25: critical range.

    These thresholds are implementation defaults, not source-defined
    clinical or industry standards.
    """
    reference_array = _validate_values(reference)
    current_array = _validate_values(current)

    if bins < 2:
        raise ValueError("bins must be at least 2.")

    if reference_array.size < 2 or current_array.size < 2:
        raise ValueError("At least two observations are required.")

    minimum = min(reference_array.min(), current_array.min())
    maximum = max(reference_array.max(), current_array.max())

    if minimum == maximum:
        return 0.0

    edges = np.linspace(minimum, maximum, bins + 1)

    reference_counts, _ = np.histogram(reference_array, bins=edges)
    current_counts, _ = np.histogram(current_array, bins=edges)

    epsilon = 1e-6

    reference_proportions = reference_counts.astype(float)
    current_proportions = current_counts.astype(float)

    reference_proportions /= reference_proportions.sum()
    current_proportions /= current_proportions.sum()

    reference_proportions = np.clip(
        reference_proportions,
        epsilon,
        None,
    )
    current_proportions = np.clip(
        current_proportions,
        epsilon,
        None,
    )

    return float(
        np.sum(
            (current_proportions - reference_proportions)
            * np.log(current_proportions / reference_proportions)
        )
    )


def calculate_ks(
    reference: Iterable[float],
    current: Iterable[float],
) -> tuple[float, float]:
    """Calculate the two-sample Kolmogorov-Smirnov statistic and p-value."""
    reference_array = _validate_values(reference)
    current_array = _validate_values(current)

    statistic, p_value = ks_2samp(
        reference_array,
        current_array,
    )

    return float(statistic), float(p_value)


def classify_psi(
    psi_value: float,
    warning_threshold: float = 0.10,
    critical_threshold: float = 0.25,
) -> str:
    """Classify PSI drift using configured implementation thresholds."""
    if psi_value < 0:
        raise ValueError("PSI cannot be negative.")

    if warning_threshold < 0 or critical_threshold < warning_threshold:
        raise ValueError("Invalid PSI thresholds.")

    if psi_value >= critical_threshold:
        return "critical"

    if psi_value >= warning_threshold:
        return "warning"

    return "stable"


def classify_ks(
    p_value: float,
    significance_level: float = 0.05,
) -> str:
    """Classify KS drift using the configured significance level."""
    if not 0 <= p_value <= 1:
        raise ValueError("KS p-value must be between 0 and 1.")

    if not 0 < significance_level < 1:
        raise ValueError("Significance level must be between 0 and 1.")

    return "warning" if p_value < significance_level else "stable"