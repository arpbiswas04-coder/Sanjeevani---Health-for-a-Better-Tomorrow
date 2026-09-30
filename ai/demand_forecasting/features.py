"""
Sanjeevani Grid - Demand Forecasting Feature Engineering
ai/demand_forecasting/features.py

Deterministic feature extraction: calendar covariates, autoregressive lags,
and leak-free rolling window statistics.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ai.demand_forecasting.config import DEFAULT_LAGS, DEFAULT_ROLLING_WINDOWS


def extract_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract deterministic calendar indicators from datetime column.
    Includes day of week, day of month, month, weekend flag, and cyclical sine/cosine encodings.
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

    # Cyclical sine/cosine transformations for periodic patterns
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7.0)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7.0)
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12.0)

    return out


def build_lag_features(
    df: pd.DataFrame,
    target_col: str = "quantity",
    lags: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Generate autoregressive lag features for target series.
    Lags are strictly backwards (positive integers) to avoid future lookahead.
    """
    if lags is None:
        lags = DEFAULT_LAGS

    out = df.copy()
    for lag in lags:
        if lag <= 0:
            raise ValueError(f"Lag values must be positive integers, got {lag}")
        out[f"lag_{lag}"] = out[target_col].shift(lag)

    return out


def build_rolling_features(
    df: pd.DataFrame,
    target_col: str = "quantity",
    windows: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Compute rolling statistics (mean, std) shifted by 1 to prevent data leakage.
    Shift(1) guarantees the current time step's target is never used in its own features.
    """
    if windows is None:
        windows = DEFAULT_ROLLING_WINDOWS

    out = df.copy()
    # Shift by 1 period before rolling to guarantee strict separation
    shifted_series = out[target_col].shift(1)

    for w in windows:
        if w <= 1:
            raise ValueError(f"Rolling window must be > 1, got {w}")
        out[f"rolling_mean_{w}"] = shifted_series.rolling(window=w, min_periods=1).mean()
        out[f"rolling_std_{w}"] = shifted_series.rolling(window=w, min_periods=1).std().fillna(0.0)

    return out


def generate_feature_matrix(
    df: pd.DataFrame,
    target_col: str = "quantity",
    lags: Optional[List[int]] = None,
    windows: Optional[List[int]] = None,
    drop_na: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generate the complete feature matrix combining calendar, lag, and rolling statistics.
    Returns the processed DataFrame and the list of generated feature column names.
    """
    if lags is None:
        lags = DEFAULT_LAGS
    if windows is None:
        windows = DEFAULT_ROLLING_WINDOWS

    out = extract_calendar_features(df)
    out = build_lag_features(out, target_col=target_col, lags=lags)
    out = build_rolling_features(out, target_col=target_col, windows=windows)

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
    feature_cols += [f"lag_{lag}" for lag in lags]
    for w in windows:
        feature_cols += [f"rolling_mean_{w}", f"rolling_std_{w}"]

    if drop_na:
        out = out.dropna(subset=feature_cols).reset_index(drop=True)

    return out, feature_cols


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "demand_forecasting.features", "status": "placeholder"}
