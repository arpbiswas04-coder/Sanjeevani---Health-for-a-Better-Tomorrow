"""Schemas for predictive procurement."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


RiskLevel = Literal[
    "low",
    "moderate",
    "high",
    "critical",
]


class ConsumptionRecord(BaseModel):
    """Historical daily consumption for one inventory item."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    quantity_consumed: float = Field(ge=0)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            raise ValueError(
                "timestamp must include timezone information."
            )

        return parsed.isoformat()


class ProcurementRequest(BaseModel):
    """Input contract for procurement prediction."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    item_id: str
    current_stock: float = Field(ge=0)
    expected_incoming: float = Field(ge=0, default=0.0)
    reserved_stock: float = Field(ge=0, default=0.0)
    unit_cost: float = Field(ge=0, default=0.0)
    history: list[ConsumptionRecord]
    horizon_days: int = Field(
        ge=1,
        le=90,
        default=7,
    )


class ProcurementForecastPoint(BaseModel):
    """Demand forecast for one future day."""

    model_config = ConfigDict(extra="forbid")

    date: str
    predicted_demand: float = Field(ge=0)
    cumulative_demand: float = Field(ge=0)
    projected_stock: float
    shortage: bool


class ProcurementResponse(BaseModel):
    """Predictive procurement recommendation."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    facility_id: str
    item_id: str
    model_version: str
    horizon_days: int

    average_daily_demand: float = Field(ge=0)
    expected_demand: float = Field(ge=0)

    current_stock: float = Field(ge=0)
    expected_incoming: float = Field(ge=0)
    reserved_stock: float = Field(ge=0)

    safety_stock: float = Field(ge=0)
    projected_stock_after_horizon: float

    suggested_procurement_quantity: float = Field(ge=0)

    expected_shortage_date: str | None
    shortage_risk: RiskLevel

    estimated_procurement_cost: float = Field(ge=0)

    forecast: list[ProcurementForecastPoint]

    explanation: list[str]

    generated_at: str