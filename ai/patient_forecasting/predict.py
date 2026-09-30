"""
Sanjeevani Grid - Patient Forecasting Inference Service
ai/patient_forecasting/predict.py

Provides the production inference contract for patient footfall forecasts.
Generates recursive multi-step forecasts with validation-derived confidence.
"""

from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ai.common.base_model import BasePredictor
from ai.common.types import format_utc_iso8601, now_utc_iso8601
from ai.patient_forecasting.data import validate_and_load_series
from ai.patient_forecasting.features import generate_feature_matrix
from ai.patient_forecasting.schema import (
    PatientForecastPoint,
    PatientForecastRequest,
    PatientForecastResponse,
)
from ai.patient_forecasting.train import XGBoostPatientForecaster


class PatientForecastingPredictor(BasePredictor):
    """
    Inference service for patient-footfall forecasting.

    Validates incoming requests and generates recursive
    multi-step daily forecasts.
    """

    def __init__(
        self,
        forecaster: Optional[XGBoostPatientForecaster] = None,
        artifact_path: Optional[Union[str, Path]] = None,
    ) -> None:

        if forecaster is not None:
            self.forecaster = forecaster

        elif artifact_path is not None:
            self.forecaster = (
                XGBoostPatientForecaster.load(
                    artifact_path
                )
            )

        else:
            self.forecaster = None

    def predict(
        self,
        payload: Union[
            Dict[str, Any],
            PatientForecastRequest,
        ],
    ) -> Dict[str, Any]:
        """
        Execute patient-footfall forecasting.

        Returns a schema-validated dictionary matching
        PatientForecastResponse.
        """

        if (
            self.forecaster is None
            or not self.forecaster.is_fitted
        ):
            raise RuntimeError(
                "PatientForecastingPredictor has no "
                "fitted model available."
            )

        # Validate the incoming request.
        if isinstance(
            payload,
            PatientForecastRequest,
        ):
            request = payload

        else:
            request = (
                PatientForecastRequest.model_validate(
                    payload
                )
            )

        # Convert historical visits into a clean DataFrame.
        df_history = (
            validate_and_load_series(
                [
                    record.model_dump()
                    for record in request.history
                ]
            )
        )

        horizon_days = request.horizon_days

        current_df = df_history.copy()

        forecast_points: List[
            PatientForecastPoint
        ] = []

        last_dt = (
            current_df["datetime"]
            .iloc[-1]
        )

        # Recursive multi-step forecasting.
        for step in range(
            1,
            horizon_days + 1,
        ):

            next_dt = (
                last_dt
                + timedelta(days=step)
            )

            # Temporary row used only to construct
            # features for the next forecast step.
            dummy_row = pd.DataFrame(
                [
                    {
                        "timestamp": format_utc_iso8601(
                            next_dt
                        ),
                        "visits": 0.0,
                        "datetime": next_dt,
                    }
                ]
            )

            extended_df = pd.concat(
                [
                    current_df,
                    dummy_row,
                ],
                ignore_index=True,
            )

            feat_df, _ = (
                generate_feature_matrix(
                    extended_df,
                    target_col="visits",
                    lags=self.forecaster.lags,
                    windows=self.forecaster.windows,
                    drop_na=False,
                )
            )

            # Select the final row representing
            # the next forecast step.
            target_features = (
                feat_df
                .iloc[[-1]]
                [
                    self.forecaster.feature_names
                ]
            )

            step_prediction = float(
                self.forecaster.predict(
                    target_features
                )[0]
            )

            step_prediction = max(
                0.0,
                step_prediction,
            )

            forecast_points.append(
                PatientForecastPoint(
                    date=format_utc_iso8601(
                        next_dt
                    ),
                    predicted_visits=round(
                        step_prediction,
                        2,
                    ),
                )
            )

            # Feed the prediction back into the
            # history for the next recursive step.
            dummy_row["visits"] = (
                step_prediction
            )

            current_df = pd.concat(
                [
                    current_df,
                    dummy_row,
                ],
                ignore_index=True,
            )

        response = PatientForecastResponse(
            facility_id=request.facility_id,
            model_version=(
                self.forecaster.model_version
            ),
            generated_at=now_utc_iso8601(),
            horizon_days=horizon_days,
            predictions=forecast_points,
            confidence=round(
                self.forecaster.confidence,
                4,
            ),
            explanation=(
                "Forecast generated from historical "
                "patient visits using calendar, "
                "autoregressive lag, and rolling "
                "features with chronological "
                "validation."
            ),
        )

        return response.model_dump()


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {
        "module": "patient_forecasting.predict",
        "status": "placeholder",
    }