"""Schemas for workforce forecasting."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import (
    ensure_uuid_v4,
    ensure_utc_iso8601,
    now_utc_iso8601,
)


Department = Literal[
    "emergency",
    "icu",
    "general_ward",
    "outpatient",
    "surgery",
    "other",
]

StaffRole = Literal[
    "doctor",
    "nurse",
    "support",
]


class WorkforceRecord(BaseModel):
    """Historical workforce observation."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    department: Department
    patient_count: float = Field(ge=0.0)
    occupancy: float = Field(
        ge=0.0,
        le=1.0,
    )
    scheduled_staff: int = Field(ge=0)
    staff_role: StaffRole

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(
        cls,
        value: str,
    ) -> str:
        return ensure_utc_iso8601(value)


class WorkforceForecastRequest(BaseModel):
    """Request for workforce requirements."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str

    history: list[WorkforceRecord] = Field(
        min_length=1
    )

    horizon_days: int = Field(
        default=7,
        ge=1,
        le=7,
    )

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(
        cls,
        value: str,
    ) -> str:
        return ensure_uuid_v4(value)


class WorkforceForecastPoint(BaseModel):
    """Forecasted workforce requirement."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    department: Department
    staff_role: StaffRole
    predicted_patients: float = Field(
        ge=0.0
    )
    required_staff: int = Field(
        ge=0
    )
    scheduled_staff: int = Field(
        ge=0
    )
    staffing_gap: int
    staffing_shortage: bool

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(
        cls,
        value: str,
    ) -> str:
        return ensure_utc_iso8601(value)


class WorkforceForecastResponse(BaseModel):
    """Workforce forecast response."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    prediction_id: str
    facility_id: str
    model_version: str
    generated_at: str
    predictions: list[WorkforceForecastPoint]
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    explanation: str

    @field_validator(
        "prediction_id",
        "facility_id",
    )
    @classmethod
    def validate_uuid(
        cls,
        value: str,
    ) -> str:
        return ensure_uuid_v4(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(
        cls,
        value: str,
    ) -> str:
        return ensure_utc_iso8601(value)


def placeholder() -> dict[str, object]:
    """Compatibility helper for the scaffold."""

    return {
        "module": "workforce_forecasting.schema",
        "status": "implemented",
    }