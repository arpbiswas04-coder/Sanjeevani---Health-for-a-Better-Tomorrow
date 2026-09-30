"""
Sanjeevani Grid - Anomaly Detection Inference Service
ai/anomaly_detection/predict.py

Production inference contract for clinical, inventory, and operational anomaly detection.
Implements BasePredictor from ai/common/base_model.py.

Supported targets (Member 3 Spec):
  - sudden_inventory_decrease
  - abnormal_consumption
  - unusual_disease_count
  - unexpected_attendance_drop
  - suspicious_manual_stock_adjustment

Deterministic Risk Level Mapping (canonical low / moderate / high / critical):
  - |Z| >= Z_CRITICAL_THRESHOLD (4.5) → CRITICAL
  - |Z| >= Z_HIGH_THRESHOLD (3.0)     → HIGH
  - |Z| >= Z_MODERATE_THRESHOLD (2.0) → MODERATE
  - |Z| <  Z_MODERATE_THRESHOLD (2.0) → LOW

The threshold values are implementation defaults defined in config.py.
They are NOT specified in the project source documents.
"""

from typing import Any, Dict, Union

from ai.anomaly_detection.config import (
    DEFAULT_MODEL_VERSION,
    DEFAULT_Z_THRESHOLD,
    Z_CRITICAL_THRESHOLD,
    Z_HIGH_THRESHOLD,
    Z_MODERATE_THRESHOLD,
)
from ai.anomaly_detection.features import compute_robust_zscore
from ai.anomaly_detection.schema import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
)
from ai.common.base_model import BasePredictor
from ai.common.types import RiskLevel, now_utc_iso8601


class AnomalyDetectorPredictor(BasePredictor):
    """
    Inference service for robust anomaly detection across clinical and supply domains.

    Validates request payloads against AnomalyDetectionRequest and returns
    a schema-validated AnomalyDetectionResponse dict.
    """

    def __init__(self, model_version: str = DEFAULT_MODEL_VERSION) -> None:
        self.model_version = model_version

    def predict(
        self,
        payload: Union[Dict[str, Any], AnomalyDetectionRequest],
    ) -> Dict[str, Any]:
        """
        Execute anomaly detection against request payload.

        Parameters
        ----------
        payload : Dict[str, Any] or AnomalyDetectionRequest
            Input payload conforming to AnomalyDetectionRequest schema.

        Returns
        -------
        dict
            Validated dictionary matching AnomalyDetectionResponse.
        """
        if isinstance(payload, AnomalyDetectionRequest):
            request = payload
        else:
            request = AnomalyDetectionRequest.model_validate(payload)

        z_thresh = request.z_threshold or DEFAULT_Z_THRESHOLD
        res = compute_robust_zscore(
            current_value=request.current_value,
            history=request.history,
            z_threshold=z_thresh,
        )

        abs_z = res["abs_z_score"]

        # Risk level determination using canonical RiskLevel
        if abs_z >= Z_CRITICAL_THRESHOLD:
            risk_level = RiskLevel.CRITICAL
        elif abs_z >= Z_HIGH_THRESHOLD:
            risk_level = RiskLevel.HIGH
        elif abs_z >= Z_MODERATE_THRESHOLD:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW

        response = AnomalyDetectionResponse(
            facility_id=request.facility_id,
            item_id=request.item_id,
            target_type=request.target_type,
            model_version=self.model_version,
            generated_at=now_utc_iso8601(),
            current_value=res["current_value"],
            baseline_median=res["baseline_median"],
            baseline_mad=res["baseline_mad"],
            z_score=res["z_score"],
            is_anomaly=res["is_anomaly"],
            risk_level=risk_level,
            direction=res["direction"],
            details={
                "z_threshold": z_thresh,
                "abs_z_score": abs_z,
                "sample_size": res["sample_size"],
            },
        )

        return response.model_dump()


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.predict", "status": "placeholder"}
