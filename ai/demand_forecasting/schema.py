"""
Sanjeevani Grid - Demand Forecasting Schemas
ai/demand_forecasting/schema.py

Defines Pydantic v2 schemas for medicine and medical-equipment demand forecasting,
adhering to docs/api/API_CONVENTIONS.md.
"""

from typing import Any, Dict, List
import uuid
from pydantic import BaseModel, Field, field_validator

from ai.common.types import (
    ensure_utc_iso8601,
    ensure_uuid_v4,
    is_valid_utc_iso8601,
    is_valid_uuid_v4,
    now_utc_iso8601,
)


class ConsumptionRecord(BaseModel):
    """Single historical consumption data point."""

    timestamp: str = Field(
        ...,
        description="UTC ISO-8601 timestamp of consumption recording (e.g. 2026-09-20T00:00:00Z)",
    )
    quantity: float = Field(
        ...,
        ge=0.0,
        description="Non-negative quantity consumed during the interval",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        return ensure_utc_iso8601(v)


class DemandForecastRequest(BaseModel):
    """Inference request schema for demand forecasting."""

    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the healthcare facility",
    )
    item_id: str = Field(
        ...,
        description="UUID v4 identifying the medicine or equipment SKU",
    )
    history: List[ConsumptionRecord] = Field(
        ...,
        min_length=7,
        description="Chronological historical consumption series (minimum 7 points)",
    )
    horizon_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Number of future daily periods to forecast",
    )

    @field_validator("facility_id", "item_id")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        return ensure_uuid_v4(v)


class ForecastPoint(BaseModel):
    """Single point in the forecasted horizon."""

    date: str = Field(
        ...,
        description="UTC ISO-8601 date string for forecasted day",
    )
    predicted_quantity: float = Field(
        ...,
        ge=0.0,
        description="Predicted point consumption value",
    )
    lower_bound: float = Field(
        ...,
        ge=0.0,
        description="Lower empirical confidence interval bound (non-negative)",
    )
    upper_bound: float = Field(
        ...,
        ge=0.0,
        description="Upper empirical confidence interval bound",
    )


class DemandForecastResponse(BaseModel):
    """Structured inference response schema for demand forecasting."""

    success: bool = Field(
        default=True,
        description="API success status indicator",
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
        description="Version tag of the XGBoost demand forecasting model",
    )
    generated_at: str = Field(
        default_factory=now_utc_iso8601,
        description="UTC ISO-8601 timestamp when prediction was generated",
    )
    horizon_days: int = Field(
        ...,
        description="Forecast horizon length in days",
    )
    predictions: List[ForecastPoint] = Field(
        ...,
        description="Daily forecasted trajectory with empirical uncertainty bounds",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Measured confidence score derived from model validation accuracy",
    )
    residual_std: float = Field(
        ...,
        ge=0.0,
        description="Empirical residual standard error from holdout validation",
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
    return {"module": "demand_forecasting.schema", "status": "placeholder"}
