"""Data validation helpers for model monitoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np


def validate_numeric_series(
    values: Sequence[float],
    *,
    name: str,
    min_size: int = 1,
) -> list[float]:
    """Validate and normalize a numeric monitoring series."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string.")

    if len(values) < min_size:
        raise ValueError(
            f"{name} must contain at least {min_size} observations."
        )

    normalized = [float(value) for value in values]

    if not np.all(np.isfinite(normalized)):
        raise ValueError(f"{name} must contain only finite numbers.")

    return normalized


def validate_feature_mapping(
    features: Mapping[str, Sequence[float]],
    *,
    min_size: int = 1,
) -> dict[str, list[float]]:
    """Validate a mapping of feature names to numeric observations."""
    if not isinstance(features, Mapping):
        raise TypeError("features must be a mapping.")

    if not features:
        raise ValueError("features cannot be empty.")

    normalized: dict[str, list[float]] = {}

    for feature_name, values in features.items():
        if not isinstance(feature_name, str) or not feature_name.strip():
            raise ValueError("Feature names must be non-empty strings.")

        normalized[feature_name] = validate_numeric_series(
            values,
            name=feature_name,
            min_size=min_size,
        )

    return normalized


def validate_matching_series_lengths(
    features: Mapping[str, Sequence[float]],
) -> int:
    """Ensure all feature series have the same number of observations."""
    if not features:
        raise ValueError("features cannot be empty.")

    lengths = {len(values) for values in features.values()}

    if len(lengths) != 1:
        raise ValueError("All feature series must have the same length.")

    return next(iter(lengths))