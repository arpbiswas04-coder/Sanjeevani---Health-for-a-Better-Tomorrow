"""Validation and normalization for risk scoring data."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from .schema import RiskIndicatorRecord


REQUIRED_COLUMNS = (
    "timestamp",
    "supply_risk",
    "bed_risk",
    "workforce_risk",
    "disease_risk",
    "anomaly_risk",
)


def validate_records(records: Iterable[RiskIndicatorRecord]) -> list[RiskIndicatorRecord]:
    """Validate and return risk indicator records."""
    validated = list(records)

    if not validated:
        raise ValueError("At least one risk indicator record is required")

    return validated


def records_to_dataframe(
    records: Iterable[RiskIndicatorRecord],
) -> pd.DataFrame:
    """Convert validated records into a deterministic DataFrame."""
    validated = validate_records(records)

    frame = pd.DataFrame(
        [record.model_dump() for record in validated]
    )

    missing = [column for column in REQUIRED_COLUMNS if column not in frame]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
    )

    numeric_columns = [
        "supply_risk",
        "bed_risk",
        "workforce_risk",
        "disease_risk",
        "anomaly_risk",
    ]

    if not frame[numeric_columns].apply(
        lambda column: column.map(pd.notna).all()
    ).all():
        raise ValueError("Risk indicators cannot contain missing values")

    frame = frame.sort_values("timestamp").reset_index(drop=True)

    return frame