"""
Sanjeevani Grid - Demand Forecasting Data Preprocessing
ai/demand_forecasting/data.py

Ingestion, chronological ordering, validation, and time-series train/test splitting
for medicine and medical equipment consumption records.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ai.common.types import ensure_utc_iso8601, is_valid_utc_iso8601
from ai.demand_forecasting.schema import ConsumptionRecord


def validate_and_load_series(
    records: Union[List[Dict[str, Any]], List[ConsumptionRecord], pd.DataFrame],
) -> pd.DataFrame:
    """
    Validate, sort chronologically, and sanitize consumption records into a DataFrame.

    Requires 'timestamp' and 'quantity' columns.
    Enforces non-negative values and finite numbers.
    """
    if isinstance(records, pd.DataFrame):
        df = records.copy()
    elif isinstance(records, list):
        if len(records) == 0:
            raise ValueError("Input consumption records list cannot be empty.")
        if isinstance(records[0], ConsumptionRecord):
            df = pd.DataFrame([r.model_dump() for r in records])
        else:
            df = pd.DataFrame(records)
    else:
        raise TypeError(f"Unsupported data type for records: {type(records).__name__}")

    if "timestamp" not in df.columns or "quantity" not in df.columns:
        raise ValueError("DataFrame must contain 'timestamp' and 'quantity' columns.")

    if len(df) == 0:
        raise ValueError("Consumption dataset has zero rows.")

    # Validate timestamps and parse to UTC datetime
    try:
        df["datetime"] = pd.to_datetime(df["timestamp"], utc=True)
    except Exception as e:
        raise ValueError(f"Failed to parse timestamps into UTC datetime: {e}")

    # Validate numeric quantities
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    if df["quantity"].isna().any():
        raise ValueError("Quantity column contains missing, non-numeric, or NaN values.")

    if not np.all(np.isfinite(df["quantity"].values)):
        raise ValueError("Quantity column contains non-finite values (Inf or -Inf).")

    if (df["quantity"] < 0.0).any():
        raise ValueError("Quantity values cannot be negative.")

    # Chronological sort and reset index
    df = df.sort_values(by="datetime").reset_index(drop=True)
    return df


def resample_daily_consumption(
    df: pd.DataFrame,
    fill_missing: str = "zero",
) -> pd.DataFrame:
    """
    Resample time series to uniform daily frequency ('1D').
    Fills missing dates with 0.0 or forward-fill.
    """
    if "datetime" not in df.columns or "quantity" not in df.columns:
        raise ValueError("DataFrame must contain 'datetime' and 'quantity' columns.")

    daily = (
        df.set_index("datetime")
        .resample("1D")
        .agg({"quantity": "sum"})
    )

    if fill_missing == "zero":
        daily["quantity"] = daily["quantity"].fillna(0.0)
    elif fill_missing == "ffill":
        daily["quantity"] = daily["quantity"].ffill().fillna(0.0)
    else:
        raise ValueError(f"Unsupported fill method: {fill_missing}")

    daily = daily.reset_index()
    daily["timestamp"] = daily["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return daily


def chronological_train_test_split(
    df: pd.DataFrame,
    test_size: Union[int, float] = 7,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split time series chronologically into train and validation sets without leakage.
    test_size can be an integer (number of rows) or float (fraction, e.g. 0.2).
    """
    n = len(df)
    if n < 4:
        raise ValueError(f"Dataset too small to split chronologically ({n} rows).")

    if isinstance(test_size, float):
        if not 0.0 < test_size < 1.0:
            raise ValueError(f"Float test_size must be between 0.0 and 1.0, got {test_size}")
        n_test = max(1, int(n * test_size))
    elif isinstance(test_size, int):
        if test_size >= n:
            raise ValueError(
                f"Test size ({test_size}) must be strictly less than total rows ({n})."
            )
        n_test = test_size
    else:
        raise TypeError("test_size must be int or float.")

    split_idx = n - n_test
    train_df = df.iloc[:split_idx].copy().reset_index(drop=True)
    test_df = df.iloc[split_idx:].copy().reset_index(drop=True)
    return train_df, test_df


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "demand_forecasting.data", "status": "placeholder"}
