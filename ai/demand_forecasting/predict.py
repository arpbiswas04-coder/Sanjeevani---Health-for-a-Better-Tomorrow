"""
Sanjeevani Grid - Demand Forecasting Inference Service
ai/demand_forecasting/predict.py

Provides the production inference contract for medicine and equipment demand forecasts.
Generates multi-step recursive forecasts with empirical uncertainty bounds and
confidence scores derived from validation residuals.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from ai.common.base_model import BasePredictor
from ai.common.types import ensure_utc_iso8601, format_utc_iso8601, now_utc_iso8601
from ai.demand_forecasting.data import validate_and_load_series
from ai.demand_forecasting.features import generate_feature_matrix
from ai.demand_forecasting.schema import (
    DemandForecastRequest,
    DemandForecastResponse,
    ForecastPoint,
)
from ai.demand_forecasting.train import XGBoostDemandForecaster


class DemandForecastingPredictor(BasePredictor):
    """
    Inference service for demand forecasting pipelines.
    Validates input payloads against Pydantic schemas and executes recursive multi-step forecasts.
    """

    def __init__(
        self,
        forecaster: Optional[XGBoostDemandForecaster] = None,
        artifact_path: Optional[Union[str, Path]] = None,
    ) -> None:
        if forecaster is not None:
            self.forecaster = forecaster
        elif artifact_path is not None:
            self.forecaster = XGBoostDemandForecaster.load(artifact_path)
        else:
            self.forecaster = None

    def predict(self, payload: Union[Dict[str, Any], DemandForecastRequest]) -> Dict[str, Any]:
        """
        Execute demand forecast against request payload.
        Returns a schema-validated dictionary matching DemandForecastResponse.
        """
        if self.forecaster is None or not self.forecaster.is_fitted:
            raise RuntimeError("DemandForecastingPredictor has no fitted model available.")

        # Validate incoming request schema
        if isinstance(payload, DemandForecastRequest):
            request = payload
        else:
            request = DemandForecastRequest.model_validate(payload)

        # Convert historical records into clean DataFrame
        df_history = validate_and_load_series([r.model_dump() for r in request.history])

        horizon_days = request.horizon_days
        current_df = df_history.copy()
        forecast_points: List[ForecastPoint] = []

        last_dt = current_df["datetime"].iloc[-1]
        sigma = self.forecaster.residual_std if self.forecaster.residual_std > 0.0 else 1.0

        # Multi-step recursive forecasting
        for step in range(1, horizon_days + 1):
            next_dt = last_dt + timedelta(days=step)
            # Create dummy row with NaN quantity to generate features for the next step
            dummy_row = pd.DataFrame([{
                "timestamp": format_utc_iso8601(next_dt),
                "quantity": 0.0,
                "datetime": next_dt,
            }])
            extended_df = pd.concat([current_df, dummy_row], ignore_index=True)

            feat_df, feature_cols = generate_feature_matrix(
                extended_df,
                lags=self.forecaster.lags,
                windows=self.forecaster.windows,
                drop_na=False,
            )

            # Extract the last row representing the target step
            target_feat = feat_df.iloc[[-1]][self.forecaster.feature_names]
            step_pred = float(self.forecaster.predict(target_feat)[0])
            step_pred = max(0.0, step_pred)

            # Empirical 95% prediction intervals (1.96 * sigma)
            lower_b = max(0.0, float(step_pred - 1.96 * sigma))
            upper_b = float(step_pred + 1.96 * sigma)

            forecast_points.append(
                ForecastPoint(
                    date=format_utc_iso8601(next_dt),
                    predicted_quantity=round(step_pred, 2),
                    lower_bound=round(lower_b, 2),
                    upper_bound=round(upper_b, 2),
                )
            )

            # Update extended row with predicted value and append to current_df
            dummy_row["quantity"] = step_pred
            current_df = pd.concat([current_df, dummy_row], ignore_index=True)

        response = DemandForecastResponse(
            facility_id=request.facility_id,
            item_id=request.item_id,
            model_version=self.forecaster.model_version,
            generated_at=now_utc_iso8601(),
            horizon_days=horizon_days,
            predictions=forecast_points,
            confidence=round(self.forecaster.confidence, 4),
            residual_std=round(self.forecaster.residual_std, 4),
        )

        return response.model_dump()


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "demand_forecasting.predict", "status": "placeholder"}
