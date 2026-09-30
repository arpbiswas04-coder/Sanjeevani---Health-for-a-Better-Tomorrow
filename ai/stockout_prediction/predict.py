"""
Sanjeevani Grid - Stockout Prediction Inference Service
ai/stockout_prediction/predict.py

Production inference contract for point-in-time stockout risk prediction.
Implements BasePredictor from ai/common/base_model.py following the same
architectural pattern as ai/demand_forecasting/predict.py.

Risk assignment is fully deterministic and traceable:
  - CRITICAL : stockout predicted AND coverage_ratio < COVERAGE_CRITICAL_THRESHOLD
  - HIGH     : stockout predicted AND coverage_ratio >= COVERAGE_CRITICAL_THRESHOLD
  - MODERATE : no stockout predicted AND coverage_ratio < COVERAGE_MODERATE_THRESHOLD
  - LOW      : no stockout predicted AND coverage_ratio >= COVERAGE_MODERATE_THRESHOLD

The threshold values (COVERAGE_CRITICAL_THRESHOLD, COVERAGE_MODERATE_THRESHOLD)
are implementation-chosen defaults defined in config.py.  They are NOT specified
by the project source-of-truth documents and should be reviewed by the team
with real operational data.

No probabilities, no confidence scores, and no learned weights are invented,
consistent with ai/AGENTS.md (Section 6).
"""

from typing import Any, Dict, Union

from ai.common.base_model import BasePredictor
from ai.common.types import RiskLevel, now_utc_iso8601
from ai.stockout_prediction.config import (
    COVERAGE_CRITICAL_THRESHOLD,
    COVERAGE_MODERATE_THRESHOLD,
    DEFAULT_MODEL_VERSION,
)
from ai.stockout_prediction.features import build_stockout_features
from ai.stockout_prediction.schema import (
    StockoutPredictionRequest,
    StockoutPredictionResponse,
)


class StockoutPredictor(BasePredictor):
    """
    Deterministic inference service for stockout risk prediction.

    Validates each request against StockoutPredictionRequest, computes
    stock-coverage features via build_stockout_features, and returns a
    schema-validated StockoutPredictionResponse dict.

    No trained model artifact is required — the scoring rule is an
    analytical reorder-point calculation that is fully explainable.
    """

    def __init__(self, model_version: str = DEFAULT_MODEL_VERSION) -> None:
        self.model_version = model_version

    def predict(
        self,
        payload: Union[Dict[str, Any], StockoutPredictionRequest],
    ) -> Dict[str, Any]:
        """
        Execute stockout prediction against a request payload.

        Parameters
        ----------
        payload : dict or StockoutPredictionRequest
            Must contain all six documented stockout inputs plus facility_id
            and item_id.

        Returns
        -------
        dict matching StockoutPredictionResponse schema.

        Raises
        ------
        pydantic.ValidationError
            If the payload fails schema validation.
        ValueError
            If feature computation encounters non-finite or negative inputs
            (defensive guard; Pydantic should catch these first).
        """
        # ── Schema validation ───────────────────────────────────────────────
        if isinstance(payload, StockoutPredictionRequest):
            request = payload
        else:
            request = StockoutPredictionRequest.model_validate(payload)

        # ── Feature computation ─────────────────────────────────────────────
        features = build_stockout_features(request.model_dump())

        available: float = features["available_quantity"]           # type: ignore[assignment]
        lead_need: float = features["demand_during_lead_time"]      # type: ignore[assignment]
        coverage_ratio: float = features["coverage_ratio"]          # type: ignore[assignment]
        days_until_stockout = features["days_until_stockout"]       # float | None

        # ── Stockout decision ───────────────────────────────────────────────
        stockout_predicted: bool = available < lead_need

        # ── Risk level assignment (canonical RiskLevel values) ──────────────
        if stockout_predicted and coverage_ratio < COVERAGE_CRITICAL_THRESHOLD:
            risk_level = RiskLevel.CRITICAL
        elif stockout_predicted:
            risk_level = RiskLevel.HIGH
        elif coverage_ratio < COVERAGE_MODERATE_THRESHOLD:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW

        # ── Build validated response ────────────────────────────────────────
        response = StockoutPredictionResponse(
            facility_id=request.facility_id,
            item_id=request.item_id,
            model_version=self.model_version,
            generated_at=now_utc_iso8601(),
            stockout_predicted=stockout_predicted,
            risk_level=risk_level,
            days_until_stockout=days_until_stockout,
            available_quantity=available,
            demand_during_lead_time=lead_need,
            coverage_ratio=round(coverage_ratio, 6),
        )
        return response.model_dump()


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.predict", "status": "placeholder"}
