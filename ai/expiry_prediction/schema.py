"""
Sanjeevani Grid - Expiry Prediction Schemas
ai/expiry_prediction/schema.py

Defines Pydantic v2 schemas for drug expiration horizon and batch spoilage risk,
adhering to docs/api/API_CONVENTIONS.md.

Documented Inputs (Member 3 Spec):
  - batch_expiry
  - batch_stock
  - current_consumption
  - forecast_consumption

Documented Outputs (Member 3 Spec):
  - likely_unused_quantity
  - wastage_risk
  - estimated_financial_loss
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import (
    RiskLevel,
    ensure_utc_iso8601,
    ensure_uuid_v4,
    now_utc_iso8601,
)


def parse_expiry_to_days(
    expiry_val: Union[str, float, int],
    reference_dt: Optional[datetime] = None,
) -> float:
    """
    Parse a batch expiry representation into non-negative floating-point days.

    Supports:
      - Direct numeric days (e.g. 30, 45.5, "60")
      - ISO-8601 UTC strings (e.g. "2026-11-15T00:00:00Z")
      - Standard date strings (e.g. "2026-11-15")
    """
    if isinstance(expiry_val, (int, float)):
        return max(0.0, float(expiry_val))
    if isinstance(expiry_val, str):
        val_clean = expiry_val.strip()
        # Direct numeric check
        try:
            return max(0.0, float(val_clean))
        except ValueError:
            pass

        # Parse date / ISO string
        ref = reference_dt or datetime.now(timezone.utc)
        clean_str = (
            val_clean[:-1] + "+00:00"
            if (val_clean.endswith("Z") or val_clean.endswith("z"))
            else val_clean
        )
        try:
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            diff_seconds = (dt - ref).total_seconds()
            return max(0.0, float(diff_seconds / 86400.0))
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Cannot parse batch expiry representation: {expiry_val!r}. "
                f"Must be numeric days or ISO-8601 date string."
            ) from exc

    raise ValueError(
        f"Unsupported type for batch expiry: {type(expiry_val).__name__}"
    )


class ExpiryPredictionRequest(BaseModel):
    """Inference request schema for batch expiration and spoilage prediction."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the healthcare facility",
    )
    item_id: str = Field(
        ...,
        description="UUID v4 identifying the medicine or clinical supply SKU",
    )
    batch_id: str = Field(
        ...,
        min_length=1,
        description="Identifier or lot number tracking this specific batch",
    )
    batch_expiry: str = Field(
        ...,
        description="Batch expiration date/timestamp (ISO-8601) or days to expiry string",
    )
    days_to_expiry: Optional[float] = Field(
        default=None,
        ge=0.0,
        allow_inf_nan=False,
        description="Explicit shelf-life duration in days (optional override)",
    )
    batch_stock: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Current quantity of units in this batch on hand",
    )
    current_consumption: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Observed current daily usage rate (units/day)",
    )
    forecast_consumption: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Projected daily consumption rate (units/day) over the remaining shelf life",
    )
    unit_cost: float = Field(
        default=0.0,
        ge=0.0,
        allow_inf_nan=False,
        description="Procurement cost per unit, used to compute estimated financial loss",
    )

    @field_validator("facility_id", "item_id")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        return ensure_uuid_v4(v)


class ExpiryPredictionResponse(BaseModel):
    """Structured inference response schema for batch expiration and spoilage risk."""

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
        description="UUID v4 identifying the evaluated SKU",
    )
    batch_id: str = Field(
        ...,
        description="Batch or lot identifier",
    )
    model_version: str = Field(
        ...,
        description="Version tag of the expiry prediction model",
    )
    generated_at: str = Field(
        default_factory=now_utc_iso8601,
        description="UTC ISO-8601 timestamp when prediction was generated",
    )
    batch_expiry: str = Field(
        ...,
        description="Batch expiration date/timestamp or descriptor",
    )
    days_to_expiry: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Days remaining before batch expiration",
    )
    batch_stock: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="On-hand batch stock evaluated",
    )
    projected_consumption: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Estimated quantity consumed prior to expiration",
    )
    likely_unused_quantity: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Projected expired/unconsumed batch units (spoilage)",
    )
    wastage_risk: RiskLevel = Field(
        ...,
        description="Canonical risk level (low / moderate / high / critical) per API_CONVENTIONS.md",
    )
    wastage_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        allow_inf_nan=False,
        description="Ratio of likely unused units to total batch stock",
    )
    estimated_financial_loss: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Monetary loss from projected unused stock (likely_unused_quantity * unit_cost)",
    )

    @field_validator("prediction_id", "facility_id", "item_id")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        return ensure_uuid_v4(v)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, v: str) -> str:
        return ensure_utc_iso8601(v)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.schema", "status": "placeholder"}
