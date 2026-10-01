"""Feature engineering for seasonal disease forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd


def create_features(
    frame: pd.DataFrame,
    *,
    lags: tuple[int, ...],
    rolling_windows: tuple[int, ...],
) -> pd.DataFrame:
    """Create calendar, seasonal, lag, and rolling features."""

    if "case_count" not in frame.columns:
        raise ValueError(
            "Input frame must contain case_count."
        )

    if frame.empty:
        raise ValueError(
            "Input frame cannot be empty."
        )

    result = frame.copy()

    index = result.index

    result["day_of_week"] = index.dayofweek
    result["day_of_month"] = index.day
    result["month"] = index.month
    result["quarter"] = index.quarter
    result["week_of_year"] = index.isocalendar().week.astype(
        int
    )

    # Cyclic encoding captures recurring annual and weekly patterns.
    result["month_sin"] = np.sin(
        2.0 * np.pi * result["month"] / 12.0
    )

    result["month_cos"] = np.cos(
        2.0 * np.pi * result["month"] / 12.0
    )

    result["week_sin"] = np.sin(
        2.0 * np.pi * result["week_of_year"] / 52.0
    )

    result["week_cos"] = np.cos(
        2.0 * np.pi * result["week_of_year"] / 52.0
    )

    result["day_of_week_sin"] = np.sin(
        2.0 * np.pi * result["day_of_week"] / 7.0
    )

    result["day_of_week_cos"] = np.cos(
        2.0 * np.pi * result["day_of_week"] / 7.0
    )

    for lag in lags:
        result[f"lag_{lag}"] = (
            result["case_count"].shift(lag)
        )

    for window in rolling_windows:
        shifted = result["case_count"].shift(1)

        result[f"rolling_mean_{window}"] = (
            shifted.rolling(window).mean()
        )

        result[f"rolling_std_{window}"] = (
            shifted.rolling(window)
            .std()
            .fillna(0.0)
        )

    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    result = result.dropna()

    return result


def get_feature_columns(
    frame: pd.DataFrame,
) -> list[str]:
    """Return model feature columns."""

    excluded = {"case_count"}

    columns = [
        column
        for column in frame.columns
        if column not in excluded
    ]

    if not columns:
        raise ValueError(
            "No feature columns available."
        )

    return columns