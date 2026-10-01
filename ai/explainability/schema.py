"""Schemas for model feature explanations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FeatureContribution(BaseModel):
    """Contribution of one feature to a model output."""

    model_config = ConfigDict(extra="forbid")

    feature: str = Field(min_length=1)
    value: float
    contribution: float
    direction: str = Field(min_length=1)


class ExplanationRequest(BaseModel):
    """Request for explaining a model prediction."""

    model_config = ConfigDict(extra="forbid")

    prediction: float
    features: dict[str, float] = Field(min_length=1)


class ExplanationResponse(BaseModel):
    """Structured explanation response."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    model_version: str
    prediction: float
    baseline: float
    contributions: list[FeatureContribution] = Field(min_length=1)
    method: str
    explanation: list[str] = Field(min_length=1)