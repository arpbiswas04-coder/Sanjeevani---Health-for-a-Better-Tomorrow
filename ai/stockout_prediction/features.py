"""
Sanjeevani Grid - Stockout Prediction Features
ai/stockout_prediction/features.py

Computes deterministic, leak-free stock-coverage features from the six
documented point-in-time inputs.  No future data or learned weights are used.

Design decisions (not specified by source-of-truth documents; documented here
as implementation choices):

  - demand_during_lead_time = daily_consumption × supplier_lead_time
      The quantity consumed while waiting for replenishment.  The project spec
      lists predicted_demand and daily_consumption as separate inputs; they are
      NOT interchangeable.  predicted_demand (a Phase 2 output) is passed
      through in the feature dict for downstream visibility but is NOT used in
      the lead-time coverage formula — that would conflate two different
      planning horizons.

  - available_quantity = current_quantity + pending_purchase_orders
                        + incoming_transfers
      Both in-transit sources reduce effective exposure.

  - coverage_ratio = available_quantity / demand_during_lead_time
      Saturates to 1.0 when demand_during_lead_time is near-zero (nothing to
      cover during the lead window, so stock is adequate by definition).
      This is an implementation default; the project spec does not define this
      ratio or its saturation behaviour.

  - days_until_stockout = available_quantity / daily_consumption
      Returns None when daily_consumption ≤ NEAR_ZERO_CONSUMPTION to prevent
      division-by-zero.  None means "consumption is near-zero; depletion
      timeline is mathematically undefined, not infinite."
"""

from typing import Dict, Mapping, Optional

import numpy as np

from ai.stockout_prediction.config import NEAR_ZERO_CONSUMPTION

# Canonical set of required input field names.
NUMERIC_FEATURES = (
    "current_quantity",
    "predicted_demand",
    "daily_consumption",
    "supplier_lead_time",
    "pending_purchase_orders",
    "incoming_transfers",
)


def build_stockout_features(values: Mapping[str, object]) -> Dict[str, object]:
    """
    Derive stock-coverage features from a point-in-time supply position.

    Parameters
    ----------
    values : Mapping[str, object]
        Must contain all six keys listed in NUMERIC_FEATURES with non-negative,
        finite numeric values.

    Returns
    -------
    dict with keys:
        current_quantity, predicted_demand, daily_consumption,
        supplier_lead_time, pending_purchase_orders, incoming_transfers,
        available_quantity, demand_during_lead_time, coverage_ratio,
        days_until_stockout (float or None)

    Raises
    ------
    ValueError
        If any required key is missing, any value is negative, or any value
        is non-finite.
    """
    missing = set(NUMERIC_FEATURES) - set(values)
    if missing:
        raise ValueError(
            f"Missing required stockout inputs: {', '.join(sorted(missing))}."
        )

    # Cast to float; reject any non-finite value immediately.
    clean: Dict[str, float] = {}
    for key in NUMERIC_FEATURES:
        try:
            val = float(values[key])  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Stockout input '{key}' must be numeric: {exc}") from exc

        if not np.isfinite(val):
            raise ValueError(
                f"Stockout input '{key}' must be finite; got {val!r}."
            )
        if val < 0.0:
            raise ValueError(
                f"Stockout input '{key}' cannot be negative; got {val!r}."
            )
        clean[key] = val

    # ── Effective stock position ────────────────────────────────────────────
    available: float = (
        clean["current_quantity"]
        + clean["pending_purchase_orders"]
        + clean["incoming_transfers"]
    )

    # ── Lead-time coverage need ─────────────────────────────────────────────
    # How much stock is consumed while waiting for the next replenishment.
    demand_during_lead_time: float = (
        clean["daily_consumption"] * clean["supplier_lead_time"]
    )

    # ── Coverage ratio ──────────────────────────────────────────────────────
    if demand_during_lead_time <= NEAR_ZERO_CONSUMPTION:
        # Lead-time window demand is effectively zero → fully covered by definition.
        coverage_ratio: float = 1.0
    else:
        coverage_ratio = available / demand_during_lead_time

    # ── Days until stockout ─────────────────────────────────────────────────
    rate: float = clean["daily_consumption"]
    days_until_stockout: Optional[float] = (
        None if rate <= NEAR_ZERO_CONSUMPTION else available / rate
    )

    return {
        **clean,
        "available_quantity": available,
        "demand_during_lead_time": demand_during_lead_time,
        "coverage_ratio": coverage_ratio,
        "days_until_stockout": days_until_stockout,
    }


def placeholder() -> Dict[str, str]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.features", "status": "placeholder"}
