"""Schemas for centralized healthcare analytics."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HistoricalTrendPoint(BaseModel):
    """A single point in a historical trend."""

    model_config = ConfigDict(extra="forbid")

    period: str = Field(min_length=1)
    value: float


class HistoricalTrendResponse(BaseModel):
    """Historical trend analytics result."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    metric_name: str = Field(min_length=1)

    points: list[HistoricalTrendPoint] = Field(
        min_length=1
    )

    total: float
    average: float
    minimum: float
    maximum: float

    change: float
    percentage_change: float | None


class UtilizationResponse(BaseModel):
    """Resource utilization analytics result."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    resource_name: str = Field(min_length=1)

    capacity: float = Field(ge=0.0)
    used: float = Field(ge=0.0)
    available: float = Field(ge=0.0)

    utilization_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    utilization_percentage: float = Field(
        ge=0.0,
        le=100.0,
    )


class CostResponse(BaseModel):
    """Cost analytics result."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    resource_name: str = Field(min_length=1)

    quantity: float = Field(ge=0.0)
    cost_per_unit: float = Field(ge=0.0)

    total_cost: float = Field(ge=0.0)
    average_cost_per_unit: float = Field(ge=0.0)


class WastageResponse(BaseModel):
    """Wastage analytics result."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    resource_name: str = Field(min_length=1)

    supplied_quantity: float = Field(ge=0.0)
    used_quantity: float = Field(ge=0.0)
    wasted_quantity: float = Field(ge=0.0)

    wastage_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    wastage_percentage: float = Field(
        ge=0.0,
        le=100.0,
    )

    wastage_cost: float = Field(ge=0.0)


class AnalyticsSummaryResponse(BaseModel):
    """Combined analytics summary."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    resource_name: str = Field(min_length=1)

    utilization_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    total_cost: float = Field(ge=0.0)

    wastage_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    wastage_cost: float = Field(ge=0.0)

    trend_change: float
    trend_percentage_change: float | None

    explanation: list[str] = Field(
        min_length=1
    )