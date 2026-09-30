"""
Sanjeevani Grid - Patient Forecasting Schemas
ai/patient_forecasting/schema.py

Defines Pydantic v2 schemas for patient footfall forecasting,
adhering to the project's shared API conventions.
"""

from typing import Any, Dict, List
import uuid

from pydantic import BaseModel, Field, field_validator

from ai.common.types import (
    ensure_utc_iso8601,
    ensure_uuid_v4,
    now_utc_iso8601,
)


class PatientVisitRecord(BaseModel):
    """Single historical patient-visit data point."""

    timestamp: str = Field(
        ...,
        description="UTC ISO-8601 timestamp of the patient visit observation",
    )
    visits: float = Field(
        ...,
        ge=0.0,
        description="Non-negative number of patient visits during the interval",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Require a valid UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(v)


class PatientForecastRequest(BaseModel):
    """Inference request schema for patient footfall forecasting."""

    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the healthcare facility",
    )
    history: List[PatientVisitRecord] = Field(
        ...,
        min_length=1,
        description="Chronological historical patient-visit series",
    )

    # Optional external factors documented for patient forecasting.
    # They are used when the corresponding data is available.
    weather: List[float] | None = Field(
        default=None,
        description="Optional weather-related feature series",
    )
    disease_trend: List[float] | None = Field(
        default=None,
        description="Optional disease-trend feature series",
    )
    local_events: List[float] | None = Field(
        default=None,
        description="Optional local-event feature series",
    )

    horizon_days: int = Field(
        default=7,
        ge=1,
        le=7,
        description="Number of future daily periods to forecast",
    )

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, v: str) -> str:
        """Require a valid UUID v4 facility identifier."""
        return ensure_uuid_v4(v)

    @field_validator(
        "weather",
        "disease_trend",
        "local_events",
    )
    @classmethod
    def validate_optional_series(
        cls,
        v: List[float] | None,
    ) -> List[float] | None:
        """Ensure optional feature values are finite numeric values."""

        if v is None:
            return None

        validated: List[float] = []

        for value in v:
            numeric = float(value)

            if numeric != numeric or numeric in (
                float("inf"),
                float("-inf"),
            ):
                raise ValueError("Optional feature values must be finite")

            validated.append(numeric)

        return validated


class PatientForecastPoint(BaseModel):
    """Single point in the predicted patient-footfall horizon."""

    date: str = Field(
        ...,
        description="UTC ISO-8601 timestamp for the forecasted day",
    )
    predicted_visits: float = Field(
        ...,
        ge=0.0,
        description="Predicted number of patient visits",
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Require a valid UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(v)


class PatientForecastResponse(BaseModel):
    """Structured inference response for patient footfall forecasting."""

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
        description="UUID v4 identifying the healthcare facility",
    )
    model_version: str = Field(
        ...,
        description="Version tag of the patient forecasting model",
    )
    generated_at: str = Field(
        default_factory=now_utc_iso8601,
        description="UTC ISO-8601 timestamp when prediction was generated",
    )
    horizon_days: int = Field(
        ...,
        ge=1,
        le=7,
        description="Forecast horizon length in days",
    )
    predictions: List[PatientForecastPoint] = Field(
        ...,
        min_length=1,
        description="Daily predicted patient-footfall trajectory",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score derived from model validation performance",
    )
    explanation: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of the forecast",
    )

    @field_validator("prediction_id", "facility_id")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        """Require valid UUID v4 identifiers."""
        return ensure_uuid_v4(v)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, v: str) -> str:
        """Require a valid UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(v)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {
        "module": "patient_forecasting.schema",
        "status": "placeholder",
    }