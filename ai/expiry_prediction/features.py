"""
Sanjeevani Grid - Expiry Prediction Features
ai/expiry_prediction/features.py

Computes deterministic, leak-free features for drug expiration horizon and
batch spoilage risk from point-in-time batch inputs.

Design decisions (not explicitly specified in source documents; documented here
as implementation choices):
  - effective_daily_rate: Uses `forecast_consumption` as the forward-looking burn
    rate if positive; falls back to `current_consumption` if forecast is 0.
  - projected_consumption = effective_daily_rate * days_to_expiry.
  - likely_unused_quantity = max(0.0, batch_stock - projected_consumption).
  - wastage_ratio = likely_unused_quantity / batch_stock (if batch_stock > 0 else 0.0).
  - estimated_financial_loss = likely_unused_quantity * unit_cost.
"""

from typing import Any, Dict, Mapping

import numpy as np

from ai.expiry_prediction.config import NEAR_ZERO_CONSUMPTION
from ai.expiry_prediction.schema import parse_expiry_to_days

EXPIRY_NUMERIC_FIELDS = (
    "batch_stock",
    "current_consumption",
    "forecast_consumption",
    "unit_cost",
)


def build_expiry_features(values: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Derive batch expiration and spoilage features from input values.

    Parameters
    ----------
    values : Mapping[str, Any]
        Must contain 'batch_stock', 'current_consumption', 'forecast_consumption',
        'unit_cost', and either 'days_to_expiry' or 'batch_expiry'.

    Returns
    -------
    dict
        Computed features including days_to_expiry, effective_daily_rate,
        projected_consumption, likely_unused_quantity, wastage_ratio,
        and estimated_financial_loss.
    """
    for field in EXPIRY_NUMERIC_FIELDS:
        if field not in values:
            raise ValueError(f"Missing required numeric field: '{field}'")
        val = float(values[field])
        if not np.isfinite(val):
            raise ValueError(f"Field '{field}' must be finite; got {val!r}")
        if val < 0.0:
            raise ValueError(f"Field '{field}' cannot be negative; got {val!r}")

    batch_stock = float(values["batch_stock"])
    current_consumption = float(values["current_consumption"])
    forecast_consumption = float(values["forecast_consumption"])
    unit_cost = float(values.get("unit_cost", 0.0))

    # Determine days to expiry
    if "days_to_expiry" in values and values["days_to_expiry"] is not None:
        days_to_expiry = float(values["days_to_expiry"])
        if not np.isfinite(days_to_expiry) or days_to_expiry < 0.0:
            raise ValueError(f"days_to_expiry must be non-negative; got {days_to_expiry!r}")
    elif "batch_expiry" in values and values["batch_expiry"] is not None:
        days_to_expiry = parse_expiry_to_days(values["batch_expiry"])
    else:
        raise ValueError("Either 'days_to_expiry' or 'batch_expiry' must be provided.")

    # Effective daily burn rate
    # Forecast consumption serves as the primary forward rate; current_consumption as fallback
    if forecast_consumption > NEAR_ZERO_CONSUMPTION:
        effective_daily_rate = forecast_consumption
    elif current_consumption > NEAR_ZERO_CONSUMPTION:
        effective_daily_rate = current_consumption
    else:
        effective_daily_rate = 0.0

    # Projected consumption until expiry
    if days_to_expiry <= 0.0 or effective_daily_rate <= 0.0:
        projected_consumption = 0.0
    else:
        projected_consumption = min(batch_stock, effective_daily_rate * days_to_expiry)

    # Likely unused quantity
    likely_unused_quantity = max(0.0, batch_stock - projected_consumption)

    # Wastage ratio
    if batch_stock <= 0.0:
        wastage_ratio = 0.0
    else:
        wastage_ratio = min(1.0, likely_unused_quantity / batch_stock)

    # Estimated financial loss
    estimated_financial_loss = likely_unused_quantity * unit_cost

    return {
        "batch_stock": batch_stock,
        "current_consumption": current_consumption,
        "forecast_consumption": forecast_consumption,
        "unit_cost": unit_cost,
        "days_to_expiry": days_to_expiry,
        "effective_daily_rate": effective_daily_rate,
        "projected_consumption": round(projected_consumption, 4),
        "likely_unused_quantity": round(likely_unused_quantity, 4),
        "wastage_ratio": round(wastage_ratio, 4),
        "estimated_financial_loss": round(estimated_financial_loss, 4),
    }


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.features", "status": "placeholder"}
