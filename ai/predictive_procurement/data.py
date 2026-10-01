"""Data preparation for predictive procurement."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from .schema import ConsumptionRecord


def records_to_dataframe(
    records: Sequence[
        ConsumptionRecord | Mapping[str, object]
    ],
) -> pd.DataFrame:
    """Convert consumption records to a daily dataframe.

    The function accepts both validated Pydantic
    ConsumptionRecord objects and dictionary payloads.
    """

    if not records:
        raise ValueError(
            "At least one consumption record is required."
        )

    rows: list[dict[str, object]] = []

    for record in records:
        if isinstance(record, ConsumptionRecord):
            timestamp = record.timestamp
            quantity = record.quantity_consumed
        elif isinstance(record, Mapping):
            if "timestamp" not in record:
                raise ValueError(
                    "Each record must contain timestamp."
                )

            if "quantity_consumed" not in record:
                raise ValueError(
                    "Each record must contain "
                    "quantity_consumed."
                )

            timestamp = record["timestamp"]
            quantity = record["quantity_consumed"]
        else:
            raise TypeError(
                "Records must be ConsumptionRecord "
                "objects or dictionaries."
            )

        rows.append(
            {
                "timestamp": timestamp,
                "quantity_consumed": quantity,
            }
        )

    frame = pd.DataFrame(rows)

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="raise",
    )

    frame["quantity_consumed"] = pd.to_numeric(
        frame["quantity_consumed"],
        errors="raise",
    )

    if (
        frame["quantity_consumed"] < 0
    ).any():
        raise ValueError(
            "quantity_consumed cannot be negative."
        )

    frame = (
        frame.sort_values("timestamp")
        .set_index("timestamp")
    )

    daily = (
        frame["quantity_consumed"]
        .resample("D")
        .sum()
    )

    return daily.to_frame(
        name="quantity_consumed"
    )


def validate_history_length(
    frame: pd.DataFrame,
    min_history_points: int,
) -> None:
    """Validate that sufficient history is available."""

    if len(frame) < min_history_points:
        raise ValueError(
            "Insufficient consumption history. "
            f"At least {min_history_points} "
            "points are required."
        )


def clean_consumption_history(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return a cleaned, non-negative consumption series."""

    if "quantity_consumed" not in frame.columns:
        raise ValueError(
            "Expected quantity_consumed column."
        )

    cleaned = frame.copy()

    cleaned["quantity_consumed"] = (
        pd.to_numeric(
            cleaned["quantity_consumed"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(lower=0.0)
    )

    return cleaned