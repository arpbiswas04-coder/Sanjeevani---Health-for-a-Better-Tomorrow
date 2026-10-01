"""Feature construction for composite resilience risk scoring."""

from __future__ import annotations

import pandas as pd

from .config import DEFAULT_CONFIG


RISK_COLUMNS = tuple(DEFAULT_CONFIG.weights.keys())


def build_risk_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build normalized risk features without changing source values."""
    missing = [column for column in RISK_COLUMNS if column not in frame.columns]

    if missing:
        raise ValueError(f"Missing risk feature columns: {missing}")

    features = frame.loc[:, RISK_COLUMNS].copy()

    for column in RISK_COLUMNS:
        features[column] = pd.to_numeric(
            features[column],
            errors="raise",
        )

        if not features[column].between(0.0, 1.0).all():
            raise ValueError(
                f"{column} must contain values between 0 and 1"
            )

    return features