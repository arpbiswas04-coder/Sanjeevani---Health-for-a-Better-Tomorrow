"""Feature engineering for workforce forecasting."""

from __future__ import annotations

import pandas as pd


def add_calendar_features(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Add calendar features."""

    data = frame.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        utc=True,
    )

    data["day_of_week"] = (
        data["date"].dt.dayofweek
    )

    data["day_of_month"] = (
        data["date"].dt.day
    )

    data["month"] = (
        data["date"].dt.month
    )

    data["weekend"] = (
        data["day_of_week"] >= 5
    ).astype(int)

    return data


def add_lag_features(
    frame: pd.DataFrame,
    lags: tuple[int, ...] = (1, 7),
) -> pd.DataFrame:
    """Add historical patient-count lag features."""

    data = frame.copy()

    data = data.sort_values(
        [
            "department",
            "staff_role",
            "date",
        ]
    )

    grouped = data.groupby(
        [
            "department",
            "staff_role",
        ],
        sort=False,
    )

    for lag in lags:
        data[f"patient_count_lag_{lag}"] = (
            grouped["patient_count"]
            .shift(lag)
        )

    return data


def add_rolling_features(
    frame: pd.DataFrame,
    windows: tuple[int, ...] = (3, 7),
) -> pd.DataFrame:
    """Add shifted rolling patient-count features."""

    data = frame.copy()

    data = data.sort_values(
        [
            "department",
            "staff_role",
            "date",
        ]
    )

    grouped = data.groupby(
        [
            "department",
            "staff_role",
        ],
        sort=False,
    )["patient_count"]

    for window in windows:
        data[
            f"patient_count_roll_mean_{window}"
        ] = (
            grouped.transform(
                lambda series: series.shift(1)
                .rolling(window)
                .mean()
            )
        )

    return data


def generate_feature_matrix(
    frame: pd.DataFrame,
    lags: tuple[int, ...] = (1, 7),
    rolling_windows: tuple[int, ...] = (3, 7),
) -> tuple[pd.DataFrame, pd.Series]:
    """Generate model features and patient-count target."""

    required = {
        "date",
        "department",
        "staff_role",
        "patient_count",
        "occupancy",
        "scheduled_staff",
    }

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    data = frame.copy()

    data = add_calendar_features(data)
    data = add_lag_features(data, lags)
    data = add_rolling_features(
        data,
        rolling_windows,
    )

    data = pd.get_dummies(
        data,
        columns=[
            "department",
            "staff_role",
        ],
        dtype=float,
    )

    target = data["patient_count"].copy()

    excluded = {
        "date",
        "patient_count",
    }

    feature_columns = [
        column
        for column in data.columns
        if column not in excluded
    ]

    features = data[
        feature_columns
    ].copy()

    valid_rows = (
        features.notna().all(axis=1)
        & target.notna()
    )

    return (
        features.loc[valid_rows].reset_index(
            drop=True
        ),
        target.loc[valid_rows].reset_index(
            drop=True
        ),
    )