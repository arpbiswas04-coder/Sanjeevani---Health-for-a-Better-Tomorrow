"""Model training for seasonal disease forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.common.metrics import (
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    calculate_wape,
)

from .config import (
    DEFAULT_CONFIG,
    SeasonalDiseaseForecastConfig,
)
from .data import chronological_split
from .features import (
    create_features,
    get_feature_columns,
)


@dataclass
class SeasonalDiseaseModel:
    """Trained seasonal disease forecasting model."""

    model: xgb.Booster
    feature_columns: list[str]
    residual_std: float
    metrics: dict[str, float]
    model_version: str


def train_model(
    frame: pd.DataFrame,
    *,
    config: SeasonalDiseaseForecastConfig = DEFAULT_CONFIG,
) -> SeasonalDiseaseModel:
    """Train a native XGBoost seasonal disease forecast model."""

    train_frame, validation_frame = chronological_split(
        frame
    )

    train_features = create_features(
        train_frame,
        lags=config.lags,
        rolling_windows=config.rolling_windows,
    )

    validation_features = create_features(
        validation_frame,
        lags=config.lags,
        rolling_windows=config.rolling_windows,
    )

    # If the validation portion does not contain enough
    # observations for the configured lag/rolling features,
    # construct features from the complete history and use
    # the final observations as validation.
    if (
        train_features.empty
        or validation_features.empty
    ):
        full_features = create_features(
            frame,
            lags=config.lags,
            rolling_windows=config.rolling_windows,
        )

        if len(full_features) < 5:
            raise ValueError(
                "Insufficient data after feature engineering."
            )

        validation_size = max(
            1,
            int(len(full_features) * 0.20),
        )

        train_features = full_features.iloc[
            :-validation_size
        ]

        validation_features = full_features.iloc[
            -validation_size:
        ]

    feature_columns = get_feature_columns(
        train_features
    )

    train_matrix = xgb.DMatrix(
        train_features[feature_columns],
        label=train_features["case_count"],
        feature_names=feature_columns,
    )

    validation_matrix = xgb.DMatrix(
        validation_features[feature_columns],
        label=validation_features["case_count"],
        feature_names=feature_columns,
    )

    parameters = {
        "objective": "reg:squarederror",
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "seed": config.random_seed,
        "nthread": 1,
        "eval_metric": "rmse",
    }

    model = xgb.train(
        params=parameters,
        dtrain=train_matrix,
        num_boost_round=300,
        evals=[
            (train_matrix, "train"),
            (validation_matrix, "validation"),
        ],
        verbose_eval=False,
    )

    actual = validation_features[
        "case_count"
    ].to_numpy(dtype=float)

    predicted = np.maximum(
        model.predict(validation_matrix),
        0.0,
    )

    residuals = actual - predicted

    residual_std = float(
        np.std(
            residuals,
            ddof=1,
        )
        if len(residuals) > 1
        else 0.0
    )

    metrics = {
        "mae": calculate_mae(
            actual,
            predicted,
        ),
        "rmse": calculate_rmse(
            actual,
            predicted,
        ),
        "mape": calculate_mape(
            actual,
            predicted,
        ),
        "wape": calculate_wape(
            actual,
            predicted,
        ),
    }

    return SeasonalDiseaseModel(
        model=model,
        feature_columns=feature_columns,
        residual_std=residual_std,
        metrics=metrics,
        model_version=config.model_version,
    )