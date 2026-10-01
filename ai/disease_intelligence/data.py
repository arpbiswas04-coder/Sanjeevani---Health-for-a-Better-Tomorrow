"""Data preparation for disease intelligence."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "timestamp",
    "disease",
    "latitude",
    "longitude",
    "case_count",
}


def validate_and_load_cases(
    records: list[dict],
) -> pd.DataFrame:
    """Validate and normalize disease observations."""

    frame = pd.DataFrame(records)

    missing = REQUIRED_COLUMNS - set(frame.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="raise",
    )

    for column in (
        "latitude",
        "longitude",
        "case_count",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    if frame["case_count"].lt(0).any():
        raise ValueError(
            "case_count cannot be negative"
        )

    if frame["latitude"].lt(-90).any() or frame[
        "latitude"
    ].gt(90).any():
        raise ValueError(
            "latitude must be between -90 and 90"
        )

    if frame["longitude"].lt(-180).any() or frame[
        "longitude"
    ].gt(180).any():
        raise ValueError(
            "longitude must be between -180 and 180"
        )

    frame["date"] = frame["timestamp"].dt.floor("D")

    return frame.sort_values(
        ["disease", "date"]
    ).reset_index(drop=True)


def aggregate_daily_cases(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate disease observations by day."""

    required = REQUIRED_COLUMNS | {"date"}

    missing = required - set(frame.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return (
        frame.groupby(
            ["date", "disease"],
            as_index=False,
        )
        .agg(
            case_count=("case_count", "sum"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .sort_values(
            ["disease", "date"]
        )
        .reset_index(drop=True)
    )