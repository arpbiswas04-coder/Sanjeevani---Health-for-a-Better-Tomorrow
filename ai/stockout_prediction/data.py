"""
Sanjeevani Grid - Stockout Prediction Data Layer
ai/stockout_prediction/data.py

Responsible for input normalization, schema validation, and safe conversion
of raw record dicts into a clean pandas DataFrame ready for feature
engineering.  All six documented stockout inputs are validated here.
"""

from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd

from ai.stockout_prediction.schema import StockoutPredictionRequest

# Numeric columns expected in every stockout record.
_NUMERIC_COLS: List[str] = [
    "current_quantity",
    "predicted_demand",
    "daily_consumption",
    "supplier_lead_time",
    "pending_purchase_orders",
    "incoming_transfers",
]


def validate_and_load_records(
    records: Iterable[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Validate an iterable of raw record dicts and return a clean DataFrame.

    Each record is validated against StockoutPredictionRequest to enforce
    field presence, type coercion, non-negativity, and UUID v4 identifiers.
    Columns facility_id and item_id are retained for traceability.

    Parameters
    ----------
    records : Iterable[dict]
        Raw record dicts, each containing the six documented stockout inputs
        plus facility_id and item_id.

    Returns
    -------
    pd.DataFrame
        Validated, normalized DataFrame with one row per record.

    Raises
    ------
    ValueError
        If the record set is empty or contains non-finite numeric values
        after Pydantic validation.
    pydantic.ValidationError
        If any individual record fails schema validation.
    """
    rows: List[Dict[str, Any]] = []
    for record in records:
        request = StockoutPredictionRequest.model_validate(record)
        rows.append(request.model_dump())

    if not rows:
        raise ValueError("Stockout dataset cannot be empty.")

    frame = pd.DataFrame(rows)

    # Defensive finite-value check after Pydantic conversion.
    numeric_values = frame[_NUMERIC_COLS].to_numpy(dtype=float)
    if not np.isfinite(numeric_values).all():
        raise ValueError(
            "Stockout feature columns must contain only finite numeric values."
        )

    return frame


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.data", "status": "placeholder"}
