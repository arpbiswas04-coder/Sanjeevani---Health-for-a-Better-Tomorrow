"""Schemas for inventory simulation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


RiskLevel = Literal[
    "low",
    "moderate",
    "high",
    "critical",
]


class InventorySimulationPoint(BaseModel):
    """Inventory state for one future date."""

    model_config = ConfigDict(extra="forbid")

    date: str
    opening_stock: float
    expected_incoming: float = Field(ge=0)
    predicted_demand: float = Field(ge=0)
    reserved_stock: float = Field(ge=0)
    closing_stock: float
    shortage: bool
    low_stock: bool


class InventorySimulationRequest(BaseModel):
    """Input contract for inventory simulation."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    item_id: str

    current_stock: float = Field(ge=0)
    reserved_stock: float = Field(ge=0, default=0.0)

    predicted_demand: list[float]
    expected_incoming: list[float] = Field(
        default_factory=list
    )

    start_date: str
    safety_stock: float = Field(ge=0, default=0.0)

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(
        cls,
        value: str,
    ) -> str:
        try:
            parsed = UUID(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "facility_id must be a valid UUID."
            ) from exc

        if parsed.version != 4:
            raise ValueError(
                "facility_id must be a UUID v4."
            )

        return str(parsed)

    @field_validator("start_date")
    @classmethod
    def validate_start_date(
        cls,
        value: str,
    ) -> str:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            raise ValueError(
                "start_date must include timezone information."
            )

        return parsed.isoformat()

    @field_validator("predicted_demand")
    @classmethod
    def validate_predicted_demand(
        cls,
        value: list[float],
    ) -> list[float]:
        if not value:
            raise ValueError(
                "predicted_demand cannot be empty."
            )

        if any(
            demand < 0
            for demand in value
        ):
            raise ValueError(
                "predicted_demand cannot contain "
                "negative values."
            )

        return value

    @field_validator("expected_incoming")
    @classmethod
    def validate_expected_incoming(
        cls,
        value: list[float],
    ) -> list[float]:
        if any(
            incoming < 0
            for incoming in value
        ):
            raise ValueError(
                "expected_incoming cannot contain "
                "negative values."
            )

        return value


class InventorySimulationResponse(BaseModel):
    """Inventory simulation result."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    facility_id: str
    item_id: str
    model_version: str

    initial_stock: float = Field(ge=0)
    reserved_stock: float = Field(ge=0)

    total_predicted_demand: float = Field(ge=0)
    total_expected_incoming: float = Field(ge=0)

    projected_ending_stock: float
    minimum_projected_stock: float

    expected_shortage_date: str | None
    shortage_days: int

    safety_stock: float = Field(ge=0)
    safety_stock_breach: bool

    risk_level: RiskLevel

    trajectory: list[InventorySimulationPoint]

    explanation: list[str]

    generated_at: str