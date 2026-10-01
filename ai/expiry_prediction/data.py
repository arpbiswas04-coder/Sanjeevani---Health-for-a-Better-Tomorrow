"""
Sanjeevani Grid - Expiry Prediction Data Layer
ai/expiry_prediction/data.py

Responsible for input validation, ingestion, and normalization of raw batch
records for expiration and spoilage risk evaluation.
"""

from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd

from ai.expiry_prediction.schema import ExpiryPredictionRequest

_NUMERIC_COLS = [
    "batch_stock",
    "current_consumption",
    "forecast_consumption",
    "unit_cost",
]


def validate_and_load_expiry_records(
    records: Iterable[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Validate raw batch records and return a normalized pandas DataFrame.

    Parameters
    ----------
    records : Iterable[Dict[str, Any]]
        Raw dictionary records matching ExpiryPredictionRequest schema.

    Returns
    -------
    pd.DataFrame
        DataFrame of validated batch records.

    Raises
    ------
    ValueError
        If the records iterable is empty or contains non-finite numeric values.
    pydantic.ValidationError
        If schema validation fails on any record.
    """
    rows: List[Dict[str, Any]] = []
    for record in records:
        req = ExpiryPredictionRequest.model_validate(record)
        rows.append(req.model_dump())

    if not rows:
        raise ValueError("Expiry records dataset cannot be empty.")

    frame = pd.DataFrame(rows)

    numeric_vals = frame[_NUMERIC_COLS].to_numpy(dtype=float)
    if not np.isfinite(numeric_vals).all():
        raise ValueError("Expiry record numeric fields must contain finite values.")

    return frame


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.data", "status": "placeholder"}
