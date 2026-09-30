"""Feature engineering for bed occupancy forecasting."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def add_calendar_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add calendar features from the observation date."""

    data = frame.copy()

    if "date" not in data.columns:
        if "timestamp" not in data.columns:
            raise ValueError("frame must contain date or timestamp.")
        data["date"] = pd.to_datetime(
            data["timestamp"],
            utc=True,
            errors="raise",
        )

    data["day_of_week"] = data["date"].dt.dayofweek
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["weekend"] = (data["day_of_week"] >= 5).astype(int)
    data["day_of_year"] = data["date"].dt.dayofyear

    data["day_of_week_sin"] = np.sin(
        2.0 * np.pi * data["day_of_week"] / 7.0
    )
    data["day_of_week_cos"] = np.cos(
        2.0 * np.pi * data["day_of_week"] / 7.0
    )

    return data


def add_lag_features(
    frame: pd.DataFrame,
    lags: Sequence[int] = (1, 2, 7),
) -> pd.DataFrame:
    """Add lagged occupancy features without using future observations."""

    data = frame.copy()

    if "occupancy" not in data.columns:
        raise ValueError("frame must contain occupancy.")

    if "bed_type" not in data.columns:
        raise ValueError("frame must contain bed_type.")

    data = data.sort_values(
        ["bed_type", "date"]
    ).reset_index(drop=True)

    for lag in lags:
        if lag <= 0:
            raise ValueError("lags must contain positive integers.")

        data[f"occupancy_lag_{lag}"] = (
            data.groupby("bed_type")["occupancy"]
            .shift(lag)
        )

    return data


def add_shifted_rolling_features(
    frame: pd.DataFrame,
    windows: Sequence[int] = (2, 7),
) -> pd.DataFrame:
    """Add historical rolling statistics shifted by one observation."""

    data = frame.copy()

    if "occupancy" not in data.columns:
        raise ValueError("frame must contain occupancy.")

    if "bed_type" not in data.columns:
        raise ValueError("frame must contain bed_type.")

    data = data.sort_values(
        ["bed_type", "date"]
    ).reset_index(drop=True)

    grouped = data.groupby("bed_type")["occupancy"]

    for window in windows:
        if window <= 0:
            raise ValueError("rolling windows must be positive integers.")

        data[f"occupancy_roll_mean_{window}"] = (
            grouped.transform(
                lambda series: series.shift(1).rolling(
                    window=window,
                    min_periods=1,
                ).mean()
            )
        )

        data[f"occupancy_roll_std_{window}"] = (
            grouped.transform(
                lambda series: series.shift(1).rolling(
                    window=window,
                    min_periods=2,
                ).std()
            )
            .fillna(0.0)
        )

    return data


def generate_feature_matrix(
    frame: pd.DataFrame,
    lags: Sequence[int] = (1, 2, 7),
    rolling_windows: Sequence[int] = (2, 7),
) -> tuple[pd.DataFrame, pd.Series]:
    """Build model features and occupancy target."""

    data = frame.copy()

    required = {
        "date",
        "bed_type",
        "total_beds",
        "occupied_beds",
        "admissions",
        "discharges",
        "emergency_cases",
        "disease_trend",
        "occupancy",
    }

    missing = required.difference(data.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data = add_calendar_features(data)
    data = add_lag_features(data, lags=lags)
    data = add_shifted_rolling_features(
        data,
        windows=rolling_windows,
    )

    # One-hot encode the three supported bed categories.
    data = pd.get_dummies(
        data,
        columns=["bed_type"],
        prefix="bed_type",
        dtype=float,
    )

    feature_columns = [
        "total_beds",
        "occupied_beds",
        "admissions",
        "discharges",
        "emergency_cases",
        "disease_trend",
        "day_of_week",
        "day_of_month",
        "month",
        "weekend",
        "day_of_year",
        "day_of_week_sin",
        "day_of_week_cos",
    ]

    feature_columns.extend(
        column
        for column in data.columns
        if column.startswith("occupancy_lag_")
        or column.startswith("occupancy_roll_")
        or column.startswith("bed_type_")
    )

    feature_columns = list(dict.fromkeys(feature_columns))

    features = data[feature_columns].copy()
    target = data["occupancy"].copy()

    # Models cannot train on the initial rows where lag features
    # are unavailable.
    valid_rows = features.notna().all(axis=1)

    features = features.loc[valid_rows].reset_index(drop=True)
    target = target.loc[valid_rows].reset_index(drop=True)

    return features, target