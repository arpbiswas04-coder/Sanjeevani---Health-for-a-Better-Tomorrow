"""
Sanjeevani Grid - Stockout Prediction Schemas
ai/stockout_prediction/schema.py

Pydantic v2 request/response contracts for the point-in-time stockout
prediction pipeline.  Adheres to docs/api/API_CONVENTIONS.md.

Inputs (per Member 3 spec):
  - current_quantity        : units on hand right now
  - predicted_demand        : aggregate demand predicted by Phase 2 (≥ 0)
  - daily_consumption       : observed average daily usage rate
  - supplier_lead_time      : days until a fresh order arrives
  - pending_purchase_orders : units already ordered but not yet received
  - incoming_transfers      : units in transit from another facility

The six inputs above are the documented stockout inputs; no other fields
may be silently added without spec authorisation.
"""

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import (
    RiskLevel,
    ensure_utc_iso8601,
    ensure_uuid_v4,
    now_utc_iso8601,
)


class StockoutPredictionRequest(BaseModel):
    """Point-in-time stock and supply position for a single item at a facility."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the healthcare facility",
    )
    item_id: str = Field(
        ...,
        description="UUID v4 identifying the medicine or equipment SKU",
    )
    current_quantity: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Units of the item currently on-hand (non-negative)",
    )
    predicted_demand: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description=(
            "Aggregate demand forecast (from Phase 2) over the planning horizon "
            "for this item; used as a secondary signal alongside daily_consumption"
        ),
    )
    daily_consumption: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Observed average daily usage rate (units per day)",
    )
    supplier_lead_time: int = Field(
        ...,
        ge=0,
        le=365,
        description="Number of days until a placed purchase order is received",
    )
    pending_purchase_orders: float = Field(
        default=0.0,
        ge=0.0,
        allow_inf_nan=False,
        description="Units already ordered but not yet received",
    )
    incoming_transfers: float = Field(
        default=0.0,
        ge=0.0,
        allow_inf_nan=False,
        description="Units in transit from another facility",
    )

    @field_validator("facility_id", "item_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        return ensure_uuid_v4(value)


class StockoutPredictionResponse(BaseModel):
    """Structured inference response for a single stockout prediction."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(
        default=True,
        description="API success status indicator per API_CONVENTIONS.md",
    )
    prediction_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID v4 tracking this prediction transaction",
    )
    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the requested healthcare facility",
    )
    item_id: str = Field(
        ...,
        description="UUID v4 identifying the forecasted medicine or equipment SKU",
    )
    model_version: str = Field(
        ...,
        description="Version tag of the stockout prediction model",
    )
    generated_at: str = Field(
        default_factory=now_utc_iso8601,
        description="UTC ISO-8601 timestamp when this prediction was generated",
    )
    stockout_predicted: bool = Field(
        ...,
        description=(
            "True when available_quantity is insufficient to cover "
            "demand_during_lead_time"
        ),
    )
    risk_level: RiskLevel = Field(
        ...,
        description=(
            "Canonical risk level (low / moderate / high / critical) "
            "per docs/api/API_CONVENTIONS.md Section 5"
        ),
    )
    days_until_stockout: Optional[float] = Field(
        default=None,
        ge=0.0,
        allow_inf_nan=False,
        description=(
            "Estimated days before available stock reaches zero at the current "
            "daily consumption rate.  None when daily_consumption is near-zero."
        ),
    )
    available_quantity: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description=(
            "Effective stock position: current_quantity + pending_purchase_orders "
            "+ incoming_transfers"
        ),
    )
    demand_during_lead_time: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description=(
            "Projected consumption over the supplier lead time window "
            "(daily_consumption × supplier_lead_time)"
        ),
    )
    coverage_ratio: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description=(
            "available_quantity / demand_during_lead_time; "
            "1.0 when demand_during_lead_time is near-zero and stock is present"
        ),
    )
    risk_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Estimated probability of stockout during supplier lead time",
    )
    predicted_shortage_quantity: float = Field(
        default=0.0,
        ge=0.0,
        description="Predicted shortage quantity if stockout occurs",
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of stockout risk decision",
    )

    @field_validator("prediction_id", "facility_id", "item_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        return ensure_uuid_v4(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: str) -> str:
        return ensure_utc_iso8601(value)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.schema", "status": "placeholder"}
