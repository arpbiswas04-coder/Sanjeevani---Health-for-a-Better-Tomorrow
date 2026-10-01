"""
Sanjeevani Grid - Expiry Prediction Inference Service
ai/expiry_prediction/predict.py

Production inference contract for batch expiration horizon and spoilage risk.
Implements BasePredictor from ai/common/base_model.py.

Outputs mandated by Member 3 specification:
  - likely unused quantity
  - wastage risk (canonical low / moderate / high / critical)
  - estimated financial loss

Risk assignment logic is fully deterministic and explainable:
  - If batch_stock <= 0: LOW (no stock at risk of spoilage)
  - If days_to_expiry <= 0 and batch_stock > 0: CRITICAL (already expired with remaining stock)
  - If wastage_ratio >= WASTAGE_CRITICAL_RATIO: CRITICAL (implementation default: >= 50% spoilage)
  - If wastage_ratio >= WASTAGE_HIGH_RATIO: HIGH (implementation default: >= 20% spoilage)
  - If wastage_ratio >= WASTAGE_MODERATE_RATIO: MODERATE (implementation default: >= 5% spoilage)
  - Else: LOW (< 5% spoilage or fully consumed)

The threshold values are implementation defaults defined in config.py.
They are NOT specified in the project source documents.
"""

from typing import Any, Dict, Union

from ai.common.base_model import BasePredictor
from ai.common.types import RiskLevel, now_utc_iso8601
from ai.expiry_prediction.config import (
    DEFAULT_MODEL_VERSION,
    WASTAGE_CRITICAL_RATIO,
    WASTAGE_HIGH_RATIO,
    WASTAGE_MODERATE_RATIO,
)
from ai.expiry_prediction.features import build_expiry_features
from ai.expiry_prediction.schema import (
    ExpiryPredictionRequest,
    ExpiryPredictionResponse,
)


class ExpiryPredictor(BasePredictor):
    """
    Inference service for drug expiration and batch spoilage risk prediction.

    Validates request payloads against ExpiryPredictionRequest and returns
    a schema-validated ExpiryPredictionResponse dict.
    """

    def __init__(self, model_version: str = DEFAULT_MODEL_VERSION) -> None:
        self.model_version = model_version

    def predict(
        self,
        payload: Union[Dict[str, Any], ExpiryPredictionRequest],
    ) -> Dict[str, Any]:
        """
        Execute expiry prediction on request payload.

        Parameters
        ----------
        payload : Dict[str, Any] or ExpiryPredictionRequest
            Batch inputs matching ExpiryPredictionRequest schema.

        Returns
        -------
        dict
            Validated dictionary matching ExpiryPredictionResponse.
        """
        # Validate schema
        if isinstance(payload, ExpiryPredictionRequest):
            request = payload
        else:
            request = ExpiryPredictionRequest.model_validate(payload)

        # Compute deterministic features
        features = build_expiry_features(request.model_dump())

        batch_stock = features["batch_stock"]
        days_to_expiry = features["days_to_expiry"]
        likely_unused_quantity = features["likely_unused_quantity"]
        wastage_ratio = features["wastage_ratio"]
        projected_consumption = features["projected_consumption"]
        estimated_financial_loss = features["estimated_financial_loss"]

        # Risk level determination
        if batch_stock <= 0.0:
            wastage_risk = RiskLevel.LOW
        elif days_to_expiry <= 0.0 and batch_stock > 0.0:
            wastage_risk = RiskLevel.CRITICAL
        elif wastage_ratio >= WASTAGE_CRITICAL_RATIO:
            wastage_risk = RiskLevel.CRITICAL
        elif wastage_ratio >= WASTAGE_HIGH_RATIO:
            wastage_risk = RiskLevel.HIGH
        elif wastage_ratio >= WASTAGE_MODERATE_RATIO:
            wastage_risk = RiskLevel.MODERATE
        else:
            wastage_risk = RiskLevel.LOW

        response = ExpiryPredictionResponse(
            facility_id=request.facility_id,
            item_id=request.item_id,
            batch_id=request.batch_id,
            model_version=self.model_version,
            generated_at=now_utc_iso8601(),
            batch_expiry=request.batch_expiry,
            days_to_expiry=round(days_to_expiry, 2),
            batch_stock=round(batch_stock, 4),
            projected_consumption=round(projected_consumption, 4),
            likely_unused_quantity=round(likely_unused_quantity, 4),
            wastage_risk=wastage_risk,
            wastage_ratio=round(wastage_ratio, 4),
            estimated_financial_loss=round(estimated_financial_loss, 2),
        )

        return response.model_dump()


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.predict", "status": "placeholder"}
