"""Pydantic schemas for composite healthcare risk scoring."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import (
    RiskLevel,
    ensure_utc_iso8601,
    ensure_uuid_v4,
)


class RiskIndicatorRecord(BaseModel):
    """Normalized risk indicators for one healthcare facility."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str

    supply_risk: float = Field(ge=0.0, le=1.0)
    bed_risk: float = Field(ge=0.0, le=1.0)
    workforce_risk: float = Field(ge=0.0, le=1.0)
    disease_risk: float = Field(ge=0.0, le=1.0)
    anomaly_risk: float = Field(ge=0.0, le=1.0)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Require a UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(value)


class RiskScoringRequest(BaseModel):
    """Inference request for facility resilience scoring."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    indicators: RiskIndicatorRecord

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, value: str) -> str:
        """Require a UUID v4 facility identifier."""
        return ensure_uuid_v4(value)


class RiskComponent(BaseModel):
    """Contribution of one risk component."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)


class RiskScoringResponse(BaseModel):
    """Composite resilience and risk scoring response."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    prediction_id: str
    facility_id: str
    model_version: str
    generated_at: str

    resilience_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel

    components: list[RiskComponent] = Field(min_length=1)
    coverage_ratio: float = Field(ge=0.0, le=1.0)
    explanation: list[str] = Field(min_length=1)

    @field_validator("prediction_id", "facility_id")
    @classmethod
    def validate_uuid_fields(cls, value: str) -> str:
        """Require UUID v4 identifiers."""
        return ensure_uuid_v4(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: str) -> str:
        """Require a UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(value)


class RiskTrainingResult(BaseModel):
    """Training/evaluation metadata for the deterministic scorer."""

    model_config = ConfigDict(extra="forbid")

    model_version: str
    sample_count: int = Field(ge=1)
    mean_risk_score: float = Field(ge=0.0, le=1.0)
    coverage_ratio: float = Field(ge=0.0, le=1.0)