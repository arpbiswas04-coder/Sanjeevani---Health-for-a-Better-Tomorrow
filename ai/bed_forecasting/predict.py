"""Inference utilities for bed occupancy forecasting."""

from __future__ import annotations

import math
from datetime import timedelta

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.bed_forecasting.config import (
    DEFAULT_CONFIG,
    BedForecastConfig,
)
from ai.bed_forecasting.features import generate_feature_matrix
from ai.bed_forecasting.schema import (
    BedForecastPoint,
    BedForecastRequest,
    BedForecastResponse,
)
from ai.bed_forecasting.train import BedTrainingResult
from ai.common.types import now_utc_iso8601


def _normal_cdf(value: float) -> float:
    """Calculate the standard normal cumulative distribution."""

    return 0.5 * (
        1.0
        + math.erf(value / math.sqrt(2.0))
    )


class BedForecastingPredictor:
    """Generate future bed occupancy predictions."""

    def __init__(
        self,
        training_result: BedTrainingResult,
        config: BedForecastConfig = DEFAULT_CONFIG,
    ) -> None:
        self.training_result = training_result
        self.config = config

    def _predict_occupancy(
        self,
        features: pd.DataFrame,
    ) -> np.ndarray:
        """Predict occupancy using the trained XGBoost model."""

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

        predictions = self.training_result.model.predict(
            model_input
        )

        return np.clip(
            predictions,
            0.0,
            1.0,
        )

    def _saturation_probability(
        self,
        predicted_occupancy: float,
        threshold: float,
    ) -> float:
        """
        Estimate probability of exceeding a saturation threshold.

        Uncertainty is based on the validation residual
        standard deviation calculated during training.
        """

        residual_std = self.training_result.residual_std

        if residual_std <= 1e-12:
            return float(
                predicted_occupancy >= threshold
            )

        z = (
            threshold - predicted_occupancy
        ) / residual_std

        probability = 1.0 - _normal_cdf(z)

        return float(
            np.clip(
                probability,
                0.0,
                1.0,
            )
        )

    def predict(
        self,
        request: BedForecastRequest,
    ) -> BedForecastResponse:
        """Generate bed occupancy forecasts."""

        if not request.history:
            raise ValueError(
                "At least one historical observation is required."
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

        history["occupancy"] = (
            history["occupied_beds"]
            / history["total_beds"]
        ).clip(
            lower=0.0,
            upper=1.0,
        )

        history = history.sort_values(
            ["bed_type", "date"]
        ).reset_index(drop=True)

        max_history = max(
            (
                *self.config.lags,
                *self.config.rolling_windows,
            ),
            default=1,
        )

        if len(history) < max_history + 1:
            raise ValueError(
                "Insufficient history for bed forecasting. "
                f"At least {max_history + 1} observations "
                "are required."
            )

        latest_date = history["date"].max()

        predictions: list[BedForecastPoint] = []

        for horizon in self.config.forecast_horizons:

            if horizon > request.horizon_days:
                continue

            target_date = (
                latest_date
                + timedelta(days=horizon)
            )

            for bed_type in (
                "icu",
                "ventilator",
                "general_ward",
            ):

                bed_history = history[
                    history["bed_type"] == bed_type
                ].copy()

                if bed_history.empty:
                    continue

                latest = bed_history.iloc[-1]

                # Future operational inputs are carried
                # forward when no future values are supplied.
                future_row = {
                    "date": target_date,
                    "bed_type": bed_type,
                    "total_beds": float(
                        latest["total_beds"]
                    ),
                    "occupied_beds": float(
                        latest["occupied_beds"]
                    ),
                    "admissions": float(
                        latest["admissions"]
                    ),
                    "discharges": float(
                        latest["discharges"]
                    ),
                    "emergency_cases": float(
                        latest["emergency_cases"]
                    ),
                    "disease_trend": float(
                        latest["disease_trend"]
                    ),
                    "occupancy": float(
                        latest["occupancy"]
                    ),
                }

                combined = pd.concat(
                    [
                        bed_history[
                            [
                                "date",
                                "bed_type",
                                "total_beds",
                                "occupied_beds",
                                "admissions",
                                "discharges",
                                "emergency_cases",
                                "disease_trend",
                                "occupancy",
                            ]
                        ],
                        pd.DataFrame([future_row]),
                    ],
                    ignore_index=True,
                )

                features, _ = generate_feature_matrix(
                    combined,
                    lags=self.config.lags,
                    rolling_windows=self.config.rolling_windows,
                )

                if features.empty:
                    continue

                latest_features = features.iloc[
                    [-1]
                ].copy()

                predicted_occupancy = float(
                    self._predict_occupancy(
                        latest_features
                    )[0]
                )

                total_beds = int(
                    latest["total_beds"]
                )

                predicted_occupied_beds = (
                    predicted_occupancy
                    * total_beds
                )

                warning_probability = (
                    self._saturation_probability(
                        predicted_occupancy,
                        self.config.saturation_warning_threshold,
                    )
                )

                critical_probability = (
                    self._saturation_probability(
                        predicted_occupancy,
                        self.config.saturation_critical_threshold,
                    )
                )

                predictions.append(
                    BedForecastPoint(
                        timestamp=(
                            target_date.isoformat()
                            .replace(
                                "+00:00",
                                "Z",
                            )
                        ),
                        bed_type=bed_type,
                        predicted_occupancy=(
                            predicted_occupancy
                        ),
                        predicted_occupied_beds=(
                            predicted_occupied_beds
                        ),
                        total_beds=total_beds,
                        warning_threshold_exceeded=(
                            warning_probability >= 0.5
                        ),
                        critical_threshold_exceeded=(
                            critical_probability >= 0.5
                        ),
                    )
                )

        return BedForecastResponse(
            success=True,
            prediction_id=str(
                __import__("uuid").uuid4()
            ),
            facility_id=request.facility_id,
            model_version="bed-forecast-xgb-v1",
            generated_at=now_utc_iso8601(),
            predictions=predictions,
            confidence=self.training_result.confidence,
            explanation=(
                "Occupancy forecasts use the trained XGBoost "
                "model. Saturation probabilities are derived "
                "from validation residual uncertainty."
            ),
        )