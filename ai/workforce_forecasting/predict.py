"""Inference utilities for workforce forecasting."""

from __future__ import annotations

import math
import uuid
from datetime import timedelta

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.common.types import now_utc_iso8601
from ai.workforce_forecasting.config import (
    DEFAULT_CONFIG,
    WorkforceForecastConfig,
)
from ai.workforce_forecasting.features import (
    generate_feature_matrix,
)
from ai.workforce_forecasting.schema import (
    WorkforceForecastPoint,
    WorkforceForecastRequest,
    WorkforceForecastResponse,
)
from ai.workforce_forecasting.train import (
    WorkforceTrainingResult,
)


def _normal_cdf(value: float) -> float:
    """Calculate the standard normal cumulative distribution."""

    return 0.5 * (
        1.0
        + math.erf(
            value / math.sqrt(2.0)
        )
    )


class WorkforceForecastingPredictor:
    """Generate workforce requirement forecasts."""

    def __init__(
        self,
        training_result: WorkforceTrainingResult,
        config: WorkforceForecastConfig = DEFAULT_CONFIG,
    ) -> None:
        self.training_result = training_result
        self.config = config

    def _predict_patient_count(
        self,
        features: pd.DataFrame,
    ) -> np.ndarray:
        """Predict future patient counts."""

        aligned_features = features.reindex(
            columns=self.training_result.feature_columns,
            fill_value=0.0,
        )

        model_input = xgb.DMatrix(
            aligned_features,
            feature_names=list(
                self.training_result.feature_columns
            ),
        )

        predictions = (
            self.training_result.model.predict(
                model_input
            )
        )

        return np.maximum(
            predictions,
            0.0,
        )

    def _confidence_from_prediction(
        self,
        predicted_patients: float,
    ) -> float:
        """Estimate uncertainty from validation residuals."""

        residual_std = (
            self.training_result.residual_std
        )

        if residual_std <= 1e-12:
            return self.training_result.confidence

        relative_error = (
            residual_std
            / max(
                abs(predicted_patients),
                1.0,
            )
        )

        return float(
            np.clip(
                1.0 - relative_error,
                0.05,
                0.99,
            )
        )

    def _required_staff(
        self,
        patient_count: float,
        staff_role: str,
    ) -> int:
        """Calculate required staff using configured ratios."""

        ratio = self.config.staff_to_patient_ratios.get(
            staff_role
        )

        if ratio is None:
            raise ValueError(
                f"No staff-to-patient ratio configured "
                f"for role '{staff_role}'."
            )

        if ratio <= 0:
            raise ValueError(
                f"Staff-to-patient ratio for "
                f"'{staff_role}' must be positive."
            )

        return int(
            math.ceil(
                patient_count / ratio
            )
        )

    def predict(
        self,
        request: WorkforceForecastRequest,
    ) -> WorkforceForecastResponse:
        """Generate workforce requirement forecasts."""

        if not request.history:
            raise ValueError(
                "At least one historical observation "
                "is required."
            )

        history = pd.DataFrame(
            [
                record.model_dump()
                for record in request.history
            ]
        )

        history["timestamp"] = pd.to_datetime(
            history["timestamp"],
            utc=True,
        )

        history["date"] = (
            history["timestamp"].dt.floor("D")
        )

        history = history.sort_values(
            [
                "department",
                "staff_role",
                "date",
            ]
        ).reset_index(drop=True)

        latest_date = history["date"].max()

        max_history = 7

        if len(history) < max_history + 1:
            raise ValueError(
                "Insufficient history for workforce "
                "forecasting. "
                f"At least {max_history + 1} "
                "observations are required."
            )

        predictions: list[
            WorkforceForecastPoint
        ] = []

        departments = sorted(
            history["department"].unique()
        )

        roles = sorted(
            history["staff_role"].unique()
        )

        for horizon in (
            self.config.forecast_horizons
        ):
            if horizon > request.horizon_days:
                continue

            target_date = (
                latest_date
                + timedelta(days=horizon)
            )

            for department in departments:
                for staff_role in roles:
                    series = history[
                        (
                            history["department"]
                            == department
                        )
                        & (
                            history["staff_role"]
                            == staff_role
                        )
                    ].copy()

                    if series.empty:
                        continue

                    latest = series.iloc[-1]

                    future_row = {
                        "date": target_date,
                        "department": department,
                        "staff_role": staff_role,
                        "patient_count": float(
                            latest["patient_count"]
                        ),
                        "occupancy": float(
                            latest["occupancy"]
                        ),
                        "scheduled_staff": int(
                            latest["scheduled_staff"]
                        ),
                    }

                    combined = pd.concat(
                        [
                            series[
                                [
                                    "date",
                                    "department",
                                    "staff_role",
                                    "patient_count",
                                    "occupancy",
                                    "scheduled_staff",
                                ]
                            ],
                            pd.DataFrame(
                                [future_row]
                            ),
                        ],
                        ignore_index=True,
                    )

                    features, _ = (
                        generate_feature_matrix(
                            combined,
                            lags=(1, 7),
                            rolling_windows=(3, 7),
                        )
                    )

                    if features.empty:
                        continue

                    latest_features = features.iloc[
                        [-1]
                    ].copy()

                    predicted_patients = float(
                        self._predict_patient_count(
                            latest_features
                        )[0]
                    )

                    required_staff = (
                        self._required_staff(
                            predicted_patients,
                            staff_role,
                        )
                    )

                    scheduled_staff = int(
                        latest["scheduled_staff"]
                    )

                    staffing_gap = (
                        required_staff
                        - scheduled_staff
                    )

                    predictions.append(
                        WorkforceForecastPoint(
                            timestamp=(
                                target_date
                                .isoformat()
                                .replace(
                                    "+00:00",
                                    "Z",
                                )
                            ),
                            department=department,
                            staff_role=staff_role,
                            predicted_patients=(
                                predicted_patients
                            ),
                            required_staff=(
                                required_staff
                            ),
                            scheduled_staff=(
                                scheduled_staff
                            ),
                            staffing_gap=(
                                staffing_gap
                            ),
                            staffing_shortage=(
                                staffing_gap > 0
                            ),
                        )
                    )

        return WorkforceForecastResponse(
            success=True,
            prediction_id=str(
                uuid.uuid4()
            ),
            facility_id=request.facility_id,
            model_version=(
                "workforce-forecast-xgb-v1"
            ),
            generated_at=now_utc_iso8601(),
            predictions=predictions,
            confidence=(
                self.training_result.confidence
            ),
            explanation=(
                "Workforce requirements are derived "
                "from forecast patient demand and "
                "configured staff-to-patient ratios. "
                "Staffing gaps compare required staff "
                "with the latest scheduled staffing."
            ),
        )