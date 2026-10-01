"""
Sanjeevani Grid - Patient Forecasting Data Preprocessing
ai/patient_forecasting/data.py

Ingestion, chronological ordering, validation, daily resampling,
and time-series train/test splitting for patient visit records.
"""

from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd

from ai.patient_forecasting.schema import PatientVisitRecord


def validate_and_load_series(
    records: Union[
        List[Dict[str, Any]],
        List[PatientVisitRecord],
        pd.DataFrame,
    ],
) -> pd.DataFrame:
    """
    Validate, sort chronologically, and sanitize patient visit records.

    Requires 'timestamp' and 'visits' columns.
    Enforces non-negative and finite visit values.
    """

    if isinstance(records, pd.DataFrame):
        df = records.copy()

    elif isinstance(records, list):
        if len(records) == 0:
            raise ValueError("Input patient visit records list cannot be empty.")

        if isinstance(records[0], PatientVisitRecord):
            df = pd.DataFrame([record.model_dump() for record in records])
        else:
            df = pd.DataFrame(records)

    else:
        raise TypeError(
            f"Unsupported data type for records: {type(records).__name__}"
        )

    if "timestamp" not in df.columns or "visits" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'timestamp' and 'visits' columns."
        )

    if len(df) == 0:
        raise ValueError("Patient visit dataset has zero rows.")

    # Parse timestamps as UTC datetime values.
    try:
        df["datetime"] = pd.to_datetime(
            df["timestamp"],
            utc=True,
        )
    except Exception as exc:
        raise ValueError(
            f"Failed to parse timestamps into UTC datetime: {exc}"
        ) from exc

    # Validate numeric visit counts.
    df["visits"] = pd.to_numeric(
        df["visits"],
        errors="coerce",
    )

    if df["visits"].isna().any():
        raise ValueError(
            "Visits column contains missing, non-numeric, or NaN values."
        )

    if not np.all(np.isfinite(df["visits"].values)):
        raise ValueError(
            "Visits column contains non-finite values (Inf or -Inf)."
        )

    if (df["visits"] < 0.0).any():
        raise ValueError("Visit values cannot be negative.")

    # Sort chronologically to prevent time-series leakage.
    df = (
        df.sort_values(by="datetime")
        .reset_index(drop=True)
    )

    return df


def resample_daily_visits(
    df: pd.DataFrame,
    fill_missing: str = "zero",
) -> pd.DataFrame:
    """
    Resample patient visits to a uniform daily frequency.

    Missing dates can be filled with:
    - 'zero': assume zero recorded visits
    - 'ffill': carry forward the latest observed value
    """

    if "datetime" not in df.columns or "visits" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'datetime' and 'visits' columns."
        )

    daily = (
        df.set_index("datetime")
        .resample("1D")
        .agg({"visits": "sum"})
    )

    if fill_missing == "zero":
        daily["visits"] = daily["visits"].fillna(0.0)

    elif fill_missing == "ffill":
        daily["visits"] = (
            daily["visits"]
            .ffill()
            .fillna(0.0)
        )

    else:
        raise ValueError(
            f"Unsupported fill method: {fill_missing}"
        )

    daily = daily.reset_index()

    daily["timestamp"] = (
        daily["datetime"]
        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    return daily


def chronological_train_test_split(
    df: pd.DataFrame,
    test_size: Union[int, float] = 7,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split patient visit time series chronologically.

    This prevents future observations from leaking into training data.

    test_size can be:
    - int: number of validation rows
    - float: fraction of the dataset, e.g. 0.2
    """

    n = len(df)

    if n < 4:
        raise ValueError(
            f"Dataset too small to split chronologically ({n} rows)."
        )

    if isinstance(test_size, float):

        if not 0.0 < test_size < 1.0:
            raise ValueError(
                "Float test_size must be between 0.0 and 1.0, "
                f"got {test_size}"
            )

        n_test = max(1, int(n * test_size))

    elif isinstance(test_size, int):

        if test_size >= n:
            raise ValueError(
                f"Test size ({test_size}) must be strictly "
                f"less than total rows ({n})."
            )

        if test_size <= 0:
            raise ValueError(
                f"Test size must be positive, got {test_size}."
            )

        n_test = test_size

    else:
        raise TypeError("test_size must be int or float.")

    split_idx = n - n_test

    train_df = (
        df.iloc[:split_idx]
        .copy()
        .reset_index(drop=True)
    )

    test_df = (
        df.iloc[split_idx:]
        .copy()
        .reset_index(drop=True)
    )

    return train_df, test_df


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {
        "module": "patient_forecasting.data",
        "status": "placeholder",
    }