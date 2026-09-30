"""Feature engineering for disease intelligence."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_growth_features(
    frame: pd.DataFrame,
    window: int = 7,
) -> pd.DataFrame:
    """Calculate disease case growth."""

    if window < 1:
        raise ValueError(
            "window must be positive"
        )

    result = frame.copy()

    result["previous_cases"] = (
        result.groupby("disease")[
            "case_count"
        ].shift(window)
    )

    result["growth_rate"] = np.where(
        result["previous_cases"] > 0,
        (
            result["case_count"]
            - result["previous_cases"]
        )
        / result["previous_cases"],
        0.0,
    )

    result["growth_rate"] = result[
        "growth_rate"
    ].replace(
        [np.inf, -np.inf],
        0.0,
    )

    return result


def add_statistical_features(
    frame: pd.DataFrame,
    window: int = 7,
) -> pd.DataFrame:
    """Calculate rolling baseline and anomaly statistics."""

    if window < 1:
        raise ValueError(
            "window must be positive"
        )

    result = frame.copy()

    grouped = result.groupby("disease")[
        "case_count"
    ]

    result["rolling_mean"] = grouped.transform(
        lambda series: (
            series.shift(1)
            .rolling(
                window,
                min_periods=3,
            )
            .mean()
        )
    )

    result["rolling_std"] = grouped.transform(
        lambda series: (
            series.shift(1)
            .rolling(
                window,
                min_periods=3,
            )
            .std()
        )
    )

    result["rolling_std"] = result[
        "rolling_std"
    ].fillna(0.0)

    result["anomaly_score"] = np.where(
        result["rolling_std"] > 0,
        (
            result["case_count"]
            - result["rolling_mean"]
        )
        / result["rolling_std"],
        0.0,
    )

    result["anomaly_score"] = (
        result["anomaly_score"]
        .replace(
            [np.inf, -np.inf],
            0.0,
        )
        .fillna(0.0)
    )

    return result


def build_disease_features(
    frame: pd.DataFrame,
    growth_window: int = 7,
) -> pd.DataFrame:
    """Build the complete disease-intelligence feature set."""

    result = add_growth_features(
        frame,
        window=growth_window,
    )

    return add_statistical_features(
        result,
        window=growth_window,
    )