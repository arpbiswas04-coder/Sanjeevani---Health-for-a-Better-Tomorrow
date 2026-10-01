"""Data preparation utilities for workforce forecasting."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from ai.workforce_forecasting.schema import (
    WorkforceRecord,
)


REQUIRED_COLUMNS = {
    "timestamp",
    "department",
    "patient_count",
    "occupancy",
    "scheduled_staff",
    "staff_role",
}


def validate_and_load_series(
    records: Iterable[
        WorkforceRecord | dict
    ],
) -> pd.DataFrame:
    """Validate workforce records and return a dataframe."""

    rows = [
        record.model_dump()
        if isinstance(record, WorkforceRecord)
        else record
        for record in records
    ]

    if not rows:
        raise ValueError(
            "At least one workforce record is required."
        )

    frame = pd.DataFrame(rows)

    missing = REQUIRED_COLUMNS.difference(
        frame.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="raise",
    )

    numeric_columns = [
        "patient_count",
        "occupancy",
        "scheduled_staff",
    ]

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    if frame[numeric_columns].isna().any().any():
        raise ValueError(
            "Workforce data contains missing numeric values."
        )

    if (
        frame["patient_count"] < 0
    ).any():
        raise ValueError(
            "patient_count cannot be negative."
        )

    if (
        frame["scheduled_staff"] < 0
    ).any():
        raise ValueError(
            "scheduled_staff cannot be negative."
        )

    if not frame["occupancy"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "occupancy must be between 0 and 1."
        )

    frame["date"] = (
        frame["timestamp"].dt.floor("D")
    )

    return frame.sort_values(
        [
            "department",
            "staff_role",
            "date",
        ]
    ).reset_index(drop=True)


def resample_daily_workforce_data(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate workforce observations to daily data."""

    required = REQUIRED_COLUMNS | {"date"}

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    data = frame.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        utc=True,
        errors="raise",
    )

    grouped = (
        data.groupby(
            [
                "department",
                "staff_role",
                "date",
            ],
            as_index=False,
        )
        .agg(
            patient_count=(
                "patient_count",
                "mean",
            ),
            occupancy=(
                "occupancy",
                "mean",
            ),
            scheduled_staff=(
                "scheduled_staff",
                "last",
            ),
        )
    )

    return grouped.sort_values(
        [
            "department",
            "staff_role",
            "date",
        ]
    ).reset_index(drop=True)