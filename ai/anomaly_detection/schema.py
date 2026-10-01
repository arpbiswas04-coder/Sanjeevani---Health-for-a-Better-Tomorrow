"""
Sanjeevani Grid - Anomaly Detection Schemas
ai/anomaly_detection/schema.py

Defines Pydantic v2 schemas for clinical, operational, and inventory anomaly detection,
adhering to docs/api/API_CONVENTIONS.md.
"""

from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.anomaly_detection.config import (
    DEFAULT_Z_THRESHOLD,
    VALID_ANOMALY_TARGETS,
)
from ai.common.types import (
    RiskLevel,
    ensure_utc_iso8601,
    ensure_uuid_v4,
    now_utc_iso8601,
)


class AnomalyDetectionRequest(BaseModel):
    """Inference request schema for anomaly detection."""

    model_config = ConfigDict(extra="forbid")

    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the healthcare facility",
    )
    item_id: str = Field(
        ...,
        description="UUID v4 identifying the item or metric entity",
    )
    target_type: str = Field(
        ...,
        description="Anomaly target domain (e.g. sudden_inventory_decrease, abnormal_consumption, unusual_disease_count, unexpected_attendance_drop, suspicious_manual_stock_adjustment)",
    )
    current_value: float = Field(
        ...,
        allow_inf_nan=False,
        description="Current observation to test for anomalous behavior",
    )
    history: List[float] = Field(
        ...,
        min_length=3,
        description="Baseline historical values used to compute distribution parameters",
    )
    z_threshold: Optional[float] = Field(
        default=DEFAULT_Z_THRESHOLD,
        gt=0.0,
        allow_inf_nan=False,
        description="Optional custom z-score cutoff for anomaly classification",
    )

    @field_validator("facility_id", "item_id")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        return ensure_uuid_v4(v)

    @field_validator("target_type")
    @classmethod
    def validate_target(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not v_clean:
            raise ValueError("target_type cannot be empty.")
        return v_clean

    @field_validator("history")
    @classmethod
    def validate_history_finite(cls, v: List[float]) -> List[float]:
        for idx, val in enumerate(v):
            if val is None or not isinstance(val, (int, float)):
                raise ValueError(f"History element at index {idx} must be numeric; got {val!r}")
        return v


class AnomalyDetectionResponse(BaseModel):
    """Structured inference response schema for anomaly detection."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(
        default=True,
        description="API success status indicator per API_CONVENTIONS.md",
    )
    prediction_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID v4 tracking this prediction transaction",
    )
    facility_id: str = Field(
        ...,
        description="UUID v4 identifying the requested healthcare facility",
    )
    item_id: str = Field(
        ...,
        description="UUID v4 identifying the evaluated item/metric",
    )
    target_type: str = Field(
        ...,
        description="Evaluated anomaly target category",
    )
    model_version: str = Field(
        ...,
        description="Version tag of the anomaly detection model",
    )
    generated_at: str = Field(
        default_factory=now_utc_iso8601,
        description="UTC ISO-8601 timestamp when prediction was generated",
    )
    current_value: float = Field(
        ...,
        allow_inf_nan=False,
        description="Observed value that was evaluated",
    )
    baseline_median: float = Field(
        ...,
        allow_inf_nan=False,
        description="Historical median baseline",
    )
    baseline_mad: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="Median Absolute Deviation of the baseline sequence",
    )
    z_score: float = Field(
        ...,
        allow_inf_nan=False,
        description="Robust z-score measuring deviation from baseline median",
    )
    is_anomaly: bool = Field(
        ...,
        description="True if absolute z-score exceeds the cutoff threshold",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Canonical risk level (low / moderate / high / critical) per API_CONVENTIONS.md",
    )
    direction: str = Field(
        ...,
        description="Direction of deviation relative to baseline ('surge', 'drop', or 'normal')",
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional diagnostic details regarding the anomaly evaluation",
    )

    @field_validator("prediction_id", "facility_id", "item_id")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        return ensure_uuid_v4(v)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, v: str) -> str:
        return ensure_utc_iso8601(v)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.schema", "status": "placeholder"}
