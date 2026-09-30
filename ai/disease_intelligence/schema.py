"""Schemas for disease intelligence and outbreak early-warning."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.common.types import (
    RiskLevel,
    ensure_utc_iso8601,
    ensure_uuid_v4,
)


class DiseaseCaseRecord(BaseModel):
    """Single disease or syndrome case observation."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    disease: str = Field(min_length=1)
    latitude: float
    longitude: float
    case_count: int = Field(ge=0)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Require a UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(value)


class DiseaseTrendPoint(BaseModel):
    """Disease trend and outbreak-warning point."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    disease: str = Field(min_length=1)
    observed_cases: int = Field(ge=0)
    expected_cases: float = Field(ge=0)
    growth_rate: float
    anomaly_score: float
    surge_probability: float = Field(
        ge=0.0,
        le=1.0,
    )
    risk_level: RiskLevel

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Require a UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(value)


class DiseaseCluster(BaseModel):
    """Geographic disease cluster."""

    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(min_length=1)
    disease: str = Field(min_length=1)
    latitude: float
    longitude: float
    case_count: int = Field(ge=0)
    member_count: int = Field(ge=1)
    radius_km: float = Field(ge=0.0)
    risk_level: RiskLevel


class DiseaseIntelligenceRequest(BaseModel):
    """Request for operational disease early-warning intelligence."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str
    disease: str = Field(min_length=1)
    history: list[DiseaseCaseRecord] = Field(min_length=1)

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, value: str) -> str:
        """Require a canonical UUID v4 facility identifier."""
        return ensure_uuid_v4(value)


class DiseaseIntelligenceResponse(BaseModel):
    """Operational disease early-warning response."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    prediction_id: str
    facility_id: str
    disease: str
    model_version: str
    generated_at: str
    current_growth_rate: float
    surge_probability: float = Field(
        ge=0.0,
        le=1.0,
    )
    risk_level: RiskLevel
    trajectory: list[DiseaseTrendPoint]
    clusters: list[DiseaseCluster]
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    explanation: list[str] = Field(min_length=1)

    @field_validator("prediction_id", "facility_id")
    @classmethod
    def validate_uuid_fields(cls, value: str) -> str:
        """Require canonical UUID v4 identifiers."""
        return ensure_uuid_v4(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: str) -> str:
        """Require a UTC ISO-8601 timestamp."""
        return ensure_utc_iso8601(value)


class DiseaseTrainingResult(BaseModel):
    """Training and validation metadata."""

    model_config = ConfigDict(extra="forbid")

    model_version: str
    metrics: dict[str, float]
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    baseline_mean: float = Field(ge=0.0)
    baseline_std: float = Field(ge=0.0)