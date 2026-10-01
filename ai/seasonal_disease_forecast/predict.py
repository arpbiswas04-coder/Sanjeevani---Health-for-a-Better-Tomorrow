"""Inference for seasonal disease forecasting."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import xgboost as xgb

from ai.common.base_model import BaseForecaster

from .config import (
    DEFAULT_CONFIG,
    SeasonalDiseaseForecastConfig,
)
from .data import (
    records_to_dataframe,
    validate_history_length,
)
from .evaluate import calculate_seasonal_signal
from .features import create_features
from .schema import (
    SeasonalDiseaseForecastPoint,
    SeasonalDiseaseForecastRequest,
    SeasonalDiseaseForecastResponse,
)
from .train import (
    SeasonalDiseaseModel,
    train_model,
)


def _validation_confidence(model_bundle: SeasonalDiseaseModel) -> float:
    """Convert validation error into a bounded confidence score.

    The score is derived from validation WAPE and is not a probability.
    Lower validation error produces higher confidence.
    """

    validation_wape = max(
        0.0,
        float(model_bundle.metrics.get("wape", 0.0)),
    )

    return float(
        1.0 / (1.0 + validation_wape)
    )


class SeasonalDiseaseForecastPredictor(
    BaseForecaster
):
    """Generate future seasonal disease-count forecasts."""

    def __init__(
        self,
        config: SeasonalDiseaseForecastConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config
        self.model_bundle: SeasonalDiseaseModel | None = None
        self.history: pd.DataFrame | None = None

    def fit(
        self,
        frame: pd.DataFrame,
    ) -> SeasonalDiseaseModel:
        """Fit the seasonal disease forecasting model."""

        validate_history_length(
            frame,
            min_history_points=(
                self.config.min_history_points
            ),
        )

        self.history = frame.copy()

        self.model_bundle = train_model(
            frame,
            config=self.config,
        )

        return self.model_bundle

    def predict(
        self,
        payload: dict,
    ) -> dict:
        """Generate a recursive future disease forecast."""

        request = (
            SeasonalDiseaseForecastRequest.model_validate(
                payload
            )
        )

        frame = records_to_dataframe(
            request.history,
            disease=request.disease,
        )

        validate_history_length(
            frame,
            min_history_points=(
                self.config.min_history_points
            ),
        )

        self.fit(frame)

        assert self.model_bundle is not None

        model = self.model_bundle.model

        feature_columns = (
            self.model_bundle.feature_columns
        )

        working = frame.copy()

        last_timestamp = working.index[-1]

        predictions: list[
            SeasonalDiseaseForecastPoint
        ] = []

        residual_std = (
            self.model_bundle.residual_std
        )

        seasonal_signal = calculate_seasonal_signal(
            frame
        )

        confidence = _validation_confidence(
            self.model_bundle
        )

        for step in range(
            1,
            request.horizon_days + 1,
        ):
            next_timestamp = (
                last_timestamp
                + timedelta(days=step)
            )

            future_index = pd.date_range(
                start=working.index[0],
                end=next_timestamp,
                freq="D",
            )

            temporary = working.reindex(
                future_index
            )

            temporary["case_count"] = (
                temporary["case_count"]
                .astype(float)
            )

            features = create_features(
                temporary,
                lags=self.config.lags,
                rolling_windows=self.config.rolling_windows,
            )

            if features.empty:
                raise ValueError(
                    "Unable to construct forecast features."
                )

            latest_features = features.iloc[
                -1:
            ][feature_columns]

            prediction_matrix = xgb.DMatrix(
                latest_features,
                feature_names=feature_columns,
            )

            predicted = float(
                max(
                    0.0,
                    model.predict(
                        prediction_matrix
                    )[0],
                )
            )

            lower_bound = max(
                0.0,
                predicted
                - (1.96 * residual_std),
            )

            upper_bound = (
                predicted
                + (1.96 * residual_std)
            )

            working.loc[
                next_timestamp,
                "case_count",
            ] = predicted

            predictions.append(
                SeasonalDiseaseForecastPoint(
                    timestamp=next_timestamp.isoformat(),
                    predicted_cases=predicted,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    confidence=confidence,
                )
            )

        response = SeasonalDiseaseForecastResponse(
            success=True,
            facility_id=request.facility_id,
            disease=request.disease,
            model_version=(
                self.model_bundle.model_version
            ),
            horizon_days=request.horizon_days,
            predictions=predictions,
            seasonal_signal=seasonal_signal,
            explanation=[
                (
                    "Forecast uses historical disease "
                    "counts, calendar seasonality, "
                    "lag features, and rolling "
                    "historical statistics."
                ),
                (
                    "Prediction bounds are derived "
                    "from validation residual variability."
                ),
                (
                    "Confidence is derived from "
                    "validation WAPE and is not a "
                    "probability."
                ),
                (
                    "Seasonal signal is a descriptive "
                    "measure of variation across "
                    "calendar months."
                ),
                (
                    "This module provides disease-trend "
                    "forecasting and is not a diagnostic "
                    "system."
                ),
            ],
        )

        return response.model_dump()


def forecast_seasonal_disease(
    *,
    facility_id: str,
    disease: str,
    history: list[dict],
    horizon_days: int = 7,
    config: SeasonalDiseaseForecastConfig = DEFAULT_CONFIG,
) -> dict:
    """Convenience function for seasonal disease forecasting."""

    predictor = SeasonalDiseaseForecastPredictor(
        config=config
    )

    payload = {
        "facility_id": facility_id,
        "disease": disease,
        "history": history,
        "horizon_days": horizon_days,
    }

    return predictor.predict(payload)