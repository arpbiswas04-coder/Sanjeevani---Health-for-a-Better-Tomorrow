"""
Sanjeevani Grid - Patient Forecasting Feature Engineering
ai/patient_forecasting/features.py

Deterministic feature extraction for patient footfall forecasting:
calendar covariates, autoregressive lags, and leak-free rolling statistics.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ai.patient_forecasting.config import (
    DEFAULT_LAGS,
    DEFAULT_ROLLING_WINDOWS,
)


def extract_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract deterministic calendar indicators from the datetime column.

    Includes:
    - day of week
    - day of month
    - month
    - weekend flag
    - day of year
    - cyclical sine/cosine encodings
    """

    if "datetime" not in df.columns:
        raise ValueError("DataFrame must contain a 'datetime' column.")

    out = df.copy()
    dt = out["datetime"].dt

    out["day_of_week"] = dt.dayofweek.astype(int)
    out["day_of_month"] = dt.day.astype(int)
    out["month"] = dt.month.astype(int)
    out["is_weekend"] = (dt.dayofweek >= 5).astype(int)
    out["day_of_year"] = dt.dayofyear.astype(int)

    # Cyclical encoding captures periodic calendar patterns.
    out["dow_sin"] = np.sin(
        2 * np.pi * out["day_of_week"] / 7.0
    )
    out["dow_cos"] = np.cos(
        2 * np.pi * out["day_of_week"] / 7.0
    )

    out["month_sin"] = np.sin(
        2 * np.pi * out["month"] / 12.0
    )
    out["month_cos"] = np.cos(
        2 * np.pi * out["month"] / 12.0
    )

    return out


def build_lag_features(
    df: pd.DataFrame,
    target_col: str = "visits",
    lags: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Generate autoregressive lag features.

    Only historical values are used, preventing future lookahead.
    """

    if lags is None:
        lags = list(DEFAULT_LAGS)

    if target_col not in df.columns:
        raise ValueError(
            f"DataFrame must contain target column '{target_col}'."
        )

    out = df.copy()

    for lag in lags:
        if lag <= 0:
            raise ValueError(
                f"Lag values must be positive integers, got {lag}"
            )

        out[f"lag_{lag}"] = out[target_col].shift(lag)

    return out


def build_rolling_features(
    df: pd.DataFrame,
    target_col: str = "visits",
    windows: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Generate leak-free rolling mean and standard deviation features.

    The target series is shifted by one period before rolling,
    ensuring the current observation is never used in its own features.
    """

    if windows is None:
        windows = list(DEFAULT_ROLLING_WINDOWS)

    if target_col not in df.columns:
        raise ValueError(
            f"DataFrame must contain target column '{target_col}'."
        )

    out = df.copy()

    # Shift first to prevent target leakage.
    shifted_series = out[target_col].shift(1)

    for window in windows:
        if window <= 1:
            raise ValueError(
                f"Rolling window must be > 1, got {window}"
            )

        out[f"rolling_mean_{window}"] = (
            shifted_series
            .rolling(window=window, min_periods=1)
            .mean()
        )

        out[f"rolling_std_{window}"] = (
            shifted_series
            .rolling(window=window, min_periods=1)
            .std()
            .fillna(0.0)
        )

    return out


def add_optional_exogenous_features(
    df: pd.DataFrame,
    weather: Optional[List[float]] = None,
    disease_trend: Optional[List[float]] = None,
    local_events: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Add optional documented external factors when supplied.

    The supplied series must align with the rows of the DataFrame.
    """

    out = df.copy()

    optional_series = {
        "weather": weather,
        "disease_trend": disease_trend,
        "local_events": local_events,
    }

    for column, values in optional_series.items():

        if values is None:
            continue

        if len(values) != len(out):
            raise ValueError(
                f"{column} series length ({len(values)}) must match "
                f"DataFrame length ({len(out)})."
            )

        numeric_values = pd.to_numeric(
            pd.Series(values),
            errors="coerce",
        )

        if numeric_values.isna().any():
            raise ValueError(
                f"{column} contains missing or non-numeric values."
            )

        if not np.all(np.isfinite(numeric_values.to_numpy())):
            raise ValueError(
                f"{column} contains non-finite values."
            )

        out[column] = numeric_values.to_numpy()

    return out


def generate_feature_matrix(
    df: pd.DataFrame,
    target_col: str = "visits",
    lags: Optional[List[int]] = None,
    windows: Optional[List[int]] = None,
    weather: Optional[List[float]] = None,
    disease_trend: Optional[List[float]] = None,
    local_events: Optional[List[float]] = None,
    drop_na: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generate the complete patient-footfall feature matrix.

    Combines:
    - calendar features
    - autoregressive lag features
    - leak-free rolling statistics
    - optional weather data
    - optional disease-trend data
    - optional local-event data
    """

    if lags is None:
        lags = list(DEFAULT_LAGS)

    if windows is None:
        windows = list(DEFAULT_ROLLING_WINDOWS)

    out = extract_calendar_features(df)

    out = add_optional_exogenous_features(
        out,
        weather=weather,
        disease_trend=disease_trend,
        local_events=local_events,
    )

    out = build_lag_features(
        out,
        target_col=target_col,
        lags=lags,
    )

    out = build_rolling_features(
        out,
        target_col=target_col,
        windows=windows,
    )

    feature_cols = [
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend",
        "day_of_year",
        "dow_sin",
        "dow_cos",
        "month_sin",
        "month_cos",
    ]

    feature_cols += [
        f"lag_{lag}"
        for lag in lags
    ]

    for window in windows:
        feature_cols += [
            f"rolling_mean_{window}",
            f"rolling_std_{window}",
        ]

    # Include optional factors only when actually supplied.
    if weather is not None:
        feature_cols.append("weather")

    if disease_trend is not None:
        feature_cols.append("disease_trend")

    if local_events is not None:
        feature_cols.append("local_events")

    if drop_na:
        out = (
            out.dropna(subset=feature_cols)
            .reset_index(drop=True)
        )

    return out, feature_cols


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {
        "module": "patient_forecasting.features",
        "status": "placeholder",
    }