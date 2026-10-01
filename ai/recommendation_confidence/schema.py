"""Schemas for recommendation confidence scoring."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ConfidenceLevel = Literal["low", "moderate", "high"]


class ConfidenceEvidence(BaseModel):
    """Individual evidence used to derive recommendation confidence."""

    model_config = ConfigDict(extra="forbid")

    validation_score: float = Field(ge=0.0, le=1.0)
    interval_coverage: float = Field(ge=0.0, le=1.0)
    target_interval_coverage: float = Field(ge=0.0, le=1.0)
    calibration_error: float = Field(ge=0.0, le=1.0)


class RecommendationConfidenceRequest(BaseModel):
    """Input evidence for confidence scoring."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)

    validation_score: float = Field(ge=0.0, le=1.0)

    interval_coverage: float = Field(ge=0.0, le=1.0)

    target_interval_coverage: float = Field(
        default=0.95,
        gt=0.0,
        le=1.0,
    )

    calibration_error: float = Field(
        ge=0.0,
        le=1.0,
    )


class RecommendationConfidenceResponse(BaseModel):
    """Transparent confidence result."""

    model_config = ConfigDict(extra="forbid")

    success: bool

    recommendation_id: str
    model_name: str
    model_version: str

    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel

    evidence: ConfidenceEvidence

    explanation: list[str] = Field(min_length=1)

    # Explicitly indicates that this score is not a probability
    # that the recommendation is correct.
    is_probability: bool = False