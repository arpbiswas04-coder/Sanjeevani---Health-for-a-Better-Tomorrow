"""Schemas for model performance and drift monitoring."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DriftStatus = Literal["stable", "warning", "critical"]


class DistributionSnapshot(BaseModel):
    """Reference or current distribution for a monitored variable."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    values: list[float] = Field(min_length=1)


class DriftMetric(BaseModel):
    """Result of a distribution drift test."""

    model_config = ConfigDict(extra="forbid")

    metric_name: Literal["psi", "ks"]
    feature_name: str = Field(min_length=1)
    value: float
    threshold: float
    status: DriftStatus


class PerformanceMetrics(BaseModel):
    """Observed model performance metrics."""

    model_config = ConfigDict(extra="forbid")

    mae: float | None = None
    rmse: float | None = None
    mape: float | None = None
    wape: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None


class ModelMonitoringRequest(BaseModel):
    """Input payload for model monitoring."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)

    reference_features: dict[str, list[float]]
    current_features: dict[str, list[float]]

    reference_predictions: list[float] = Field(min_length=1)
    current_predictions: list[float] = Field(min_length=1)

    reference_performance: PerformanceMetrics | None = None
    current_performance: PerformanceMetrics | None = None


class ModelMonitoringResponse(BaseModel):
    """Frontend/backend-friendly monitoring result."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    model_name: str
    model_version: str
    overall_status: DriftStatus

    drift_metrics: list[DriftMetric]
    performance_degradation: dict[str, float]

    retraining_recommended: bool

    explanation: list[str] = Field(min_length=1)