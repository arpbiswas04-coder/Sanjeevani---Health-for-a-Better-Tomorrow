"""Data preparation utilities for bed occupancy forecasting."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from ai.bed_forecasting.schema import BedOccupancyRecord


REQUIRED_COLUMNS = {
    "timestamp",
    "bed_type",
    "total_beds",
    "occupied_beds",
    "admissions",
    "discharges",
    "emergency_cases",
    "disease_trend",
}


def validate_and_load_series(
    records: Iterable[BedOccupancyRecord | dict],
) -> pd.DataFrame:
    """Validate bed observations and return a sorted DataFrame."""

    rows = [
        record.model_dump() if isinstance(record, BedOccupancyRecord) else record
        for record in records
    ]

    if not rows:
        raise ValueError("At least one bed occupancy record is required.")

    frame = pd.DataFrame(rows)

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="raise",
    )

    numeric_columns = [
        "total_beds",
        "occupied_beds",
        "admissions",
        "discharges",
        "emergency_cases",
        "disease_trend",
    ]

    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")

        if not frame[column].map(pd.api.types.is_number).all():
            raise ValueError(f"{column} contains non-numeric values.")

        if not frame[column].map(pd.notna).all():
            raise ValueError(f"{column} contains missing values.")

    if (frame["total_beds"] <= 0).any():
        raise ValueError("total_beds must be greater than zero.")

    for column in [
        "occupied_beds",
        "admissions",
        "discharges",
        "emergency_cases",
    ]:
        if (frame[column] < 0).any():
            raise ValueError(f"{column} cannot contain negative values.")

    if (frame["occupied_beds"] > frame["total_beds"]).any():
        raise ValueError("occupied_beds cannot exceed total_beds.")

    frame["occupancy"] = (
        frame["occupied_beds"] / frame["total_beds"]
    ).clip(lower=0.0, upper=1.0)

    return frame.sort_values(
        ["bed_type", "timestamp"]
    ).reset_index(drop=True)


def resample_daily_bed_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observations to one daily observation per bed type."""

    required = REQUIRED_COLUMNS | {"timestamp"}
    missing = required.difference(frame.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data = frame.copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
        errors="raise",
    )

    data["date"] = data["timestamp"].dt.floor("D")

    grouped = (
        data.groupby(["bed_type", "date"], as_index=False)
        .agg(
            total_beds=("total_beds", "last"),
            occupied_beds=("occupied_beds", "last"),
            admissions=("admissions", "sum"),
            discharges=("discharges", "sum"),
            emergency_cases=("emergency_cases", "sum"),
            disease_trend=("disease_trend", "mean"),
        )
    )

    grouped["occupancy"] = (
        grouped["occupied_beds"] / grouped["total_beds"]
    ).clip(lower=0.0, upper=1.0)

    return grouped.sort_values(
        ["bed_type", "date"]
    ).reset_index(drop=True)


def chronological_train_test_split(
    frame: pd.DataFrame,
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split observations chronologically without future-data leakage."""

    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1.")

    if len(frame) < 2:
        raise ValueError("At least two observations are required.")

    data = frame.sort_values("date").reset_index(drop=True)

    split_index = max(
        1,
        min(
            len(data) - 1,
            int(len(data) * (1.0 - test_fraction)),
        ),
    )

    return data.iloc[:split_index].copy(), data.iloc[split_index:].copy()