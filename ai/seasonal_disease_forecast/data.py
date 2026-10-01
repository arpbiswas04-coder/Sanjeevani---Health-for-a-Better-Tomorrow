"""Data preparation for seasonal disease forecasting."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .schema import SeasonalDiseaseRecord


def records_to_dataframe(
    records: Sequence[SeasonalDiseaseRecord],
    *,
    disease: str,
) -> pd.DataFrame:
    """Convert validated disease records into a daily time series."""

    if not records:
        raise ValueError(
            "records cannot be empty."
        )

    if not disease.strip():
        raise ValueError(
            "disease cannot be empty."
        )

    rows = []

    for record in records:
        if record.disease != disease:
            continue

        rows.append(
            {
                "timestamp": pd.to_datetime(
                    record.timestamp,
                    utc=True,
                ),
                "case_count": float(
                    record.case_count
                ),
            }
        )

    if not rows:
        raise ValueError(
            "No records found for the requested disease."
        )

    frame = pd.DataFrame(rows)

    frame = (
        frame.groupby("timestamp", as_index=False)[
            "case_count"
        ]
        .sum()
        .sort_values("timestamp")
    )

    frame = frame.set_index("timestamp")

    # Fill missing calendar days with zero observations.
    frame = frame.resample("D").sum()

    frame["case_count"] = (
        frame["case_count"]
        .clip(lower=0.0)
        .astype(float)
    )

    return frame


def validate_history_length(
    frame: pd.DataFrame,
    *,
    min_history_points: int,
) -> None:
    """Ensure sufficient historical observations exist."""

    if len(frame) < min_history_points:
        raise ValueError(
            "Insufficient historical data. "
            f"At least {min_history_points} daily observations "
            "are required."
        )


def chronological_split(
    frame: pd.DataFrame,
    *,
    validation_fraction: float = 0.20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a time series without shuffling."""

    if not 0.0 < validation_fraction < 1.0:
        raise ValueError(
            "validation_fraction must be between 0 and 1."
        )

    if len(frame) < 5:
        raise ValueError(
            "At least five observations are required "
            "for chronological splitting."
        )

    split_index = int(
        len(frame) * (1.0 - validation_fraction)
    )

    split_index = max(
        1,
        min(split_index, len(frame) - 1),
    )

    train = frame.iloc[:split_index].copy()
    validation = frame.iloc[split_index:].copy()

    return train, validation