"""Input validation and normalization for explainability."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def validate_features(
    features: Mapping[str, float],
) -> dict[str, float]:
    """Validate feature names and finite numeric values."""
    if not features:
        raise ValueError("At least one feature is required")

    normalized: dict[str, float] = {}

    for name, value in features.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Feature names must be non-empty strings")

        numeric_value = float(value)

        if not np.isfinite(numeric_value):
            raise ValueError(
                f"Feature '{name}' must contain a finite value"
            )

        normalized[name] = numeric_value

    return normalized


def features_to_dataframe(
    features: Mapping[str, float],
) -> pd.DataFrame:
    """Convert validated features to a single-row DataFrame."""
    normalized = validate_features(features)
    return pd.DataFrame([normalized])