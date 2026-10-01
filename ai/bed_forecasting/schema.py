"""Schemas for bed occupancy forecasting."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import ensure_utc_iso8601, ensure_uuid_v4, now_utc_iso8601


BedType = Literal["icu", "ventilator", "general_ward"]


class BedOccupancyRecord(BaseModel):
    """Historical occupancy observation for one bed category."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    bed_type: BedType
    total_beds: int = Field(gt=0)
    occupied_beds: int = Field(ge=0)
    admissions: float = Field(ge=0)
    discharges: float = Field(ge=0)
    emergency_cases: float = Field(ge=0)
    disease_trend: float = 0.0

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        return ensure_utc_iso8601(value)

    @field_validator("occupied_beds")
    @classmethod
    def validate_occupied_beds(cls, value: int, info) -> int:
        total_beds = info.data.get("total_beds")
        if total_beds is not None and value > total_beds:
            raise ValueError("occupied_beds cannot exceed total_beds")
        return value


class BedForecastRequest(BaseModel):
    """Request for future bed occupancy projections."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    history: list[BedOccupancyRecord] = Field(min_length=1)
    horizon_days: int = Field(default=7, ge=1, le=7)

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, value: str) -> str:
        return ensure_uuid_v4(value)


class BedForecastPoint(BaseModel):
    """Predicted occupancy for one future horizon."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    bed_type: BedType

    predicted_occupancy: float = Field(
        ge=0.0,
        le=1.0,
    )

    predicted_occupied_beds: float = Field(
        ge=0.0,
    )

    total_beds: int = Field(
        gt=0,
    )

    warning_saturation_probability: float = Field(
        ge=0.0,
        le=1.0,
    )

    critical_saturation_probability: float = Field(
        ge=0.0,
        le=1.0,
    )

    warning_threshold_exceeded: bool
    critical_threshold_exceeded: bool

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        return ensure_utc_iso8601(value)


class BedForecastResponse(BaseModel):
    """Standard AI response for bed occupancy forecasting."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True

    prediction_id: str

    facility_id: str

    model_version: str

    generated_at: str

    predictions: list[BedForecastPoint]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    explanation: str

    @field_validator("prediction_id", "facility_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        return ensure_uuid_v4(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: str) -> str:
        return ensure_utc_iso8601(value)


def placeholder() -> dict[str, object]:
    """Backward-compatible placeholder helper."""

    return {
        "module": "bed_forecasting.schema",
        "status": "implemented",
    }