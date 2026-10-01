"""Schemas for seasonal disease forecasting."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SeasonalDiseaseRecord(BaseModel):
    """Historical disease observation."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(min_length=1)
    disease: str = Field(min_length=1)
    case_count: float = Field(ge=0.0)


class SeasonalDiseaseForecastRequest(BaseModel):
    """Request for seasonal disease forecasting."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str = Field(min_length=1)
    disease: str = Field(min_length=1)

    history: list[SeasonalDiseaseRecord] = Field(
        min_length=1
    )

    horizon_days: int = Field(
        default=7,
        gt=0,
    )


class SeasonalDiseaseForecastPoint(BaseModel):
    """One forecasted disease-count point."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(min_length=1)

    predicted_cases: float = Field(
        ge=0.0
    )

    lower_bound: float = Field(
        ge=0.0
    )

    upper_bound: float = Field(
        ge=0.0
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class SeasonalDiseaseForecastResponse(BaseModel):
    """Seasonal disease forecast response."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    facility_id: str
    disease: str

    model_version: str

    horizon_days: int

    predictions: list[
        SeasonalDiseaseForecastPoint
    ] = Field(min_length=1)

    seasonal_signal: float

    explanation: list[str] = Field(
        min_length=1
    )