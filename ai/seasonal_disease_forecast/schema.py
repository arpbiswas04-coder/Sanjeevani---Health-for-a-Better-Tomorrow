"""Schemas for seasonal disease forecasting."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import (
    ensure_utc_iso8601,
    ensure_uuid_v4,
)


class SeasonalDiseaseRecord(BaseModel):
    """Historical disease observation."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(min_length=1)
    disease: str = Field(min_length=1)
    case_count: float = Field(ge=0.0)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Require a UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(value)


class SeasonalDiseaseForecastRequest(BaseModel):
    """Request for seasonal disease forecasting."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str = Field(min_length=1)
    disease: str = Field(min_length=1)

    history: list[SeasonalDiseaseRecord] = Field(
        min_length=1,
    )

    horizon_days: int = Field(
        default=7,
        gt=0,
    )

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, value: str) -> str:
        """Require a canonical UUID v4 facility identifier."""
        return ensure_uuid_v4(value)


class SeasonalDiseaseForecastPoint(BaseModel):
    """One forecasted disease-count point."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(min_length=1)

    predicted_cases: float = Field(
        ge=0.0,
    )

    lower_bound: float = Field(
        ge=0.0,
    )

    upper_bound: float = Field(
        ge=0.0,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Require a UTC ISO-8601 forecast timestamp."""
        return ensure_utc_iso8601(value)


class SeasonalDiseaseForecastResponse(BaseModel):
    """Seasonal disease forecast response."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    facility_id: str
    disease: str

    model_version: str

    horizon_days: int

    predictions: list[SeasonalDiseaseForecastPoint] = Field(
        min_length=1,
    )

    seasonal_signal: float

    explanation: list[str] = Field(
        min_length=1,
    )

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, value: str) -> str:
        """Require a canonical UUID v4 facility identifier."""
        return ensure_uuid_v4(value)