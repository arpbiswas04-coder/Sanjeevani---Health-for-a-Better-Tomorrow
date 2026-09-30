"""Training pipeline for workforce forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.workforce_forecasting.config import (
    DEFAULT_CONFIG,
    WorkforceForecastConfig,
)
from ai.workforce_forecasting.features import (
    generate_feature_matrix,
)


@dataclass(frozen=True)
class WorkforceTrainingResult:
    """Result returned after workforce model training."""

    model: xgb.Booster
    feature_columns: tuple[str, ...]
    metrics: dict[str, float]
    residual_std: float
    confidence: float


def _calculate_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Calculate forecasting metrics."""

    errors = predicted - actual

    mae = float(
        np.mean(np.abs(errors))
    )

    rmse = float(
        np.sqrt(np.mean(errors**2))
    )

    non_zero = np.abs(actual) > 1e-8

    if non_zero.any():
        mape = float(
            np.mean(
                np.abs(
                    (
                        actual[non_zero]
                        - predicted[non_zero]
                    )
                    / actual[non_zero]
                )
            )
            * 100.0
        )
    else:
        mape = 0.0

    denominator = float(
        np.sum(np.abs(actual))
    )

    if denominator > 1e-8:
        wape = float(
            np.sum(np.abs(errors))
            / denominator
            * 100.0
        )
    else:
        wape = 0.0

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "wape": wape,
    }


def _prepare_training_frame(
    frame: pd.DataFrame,
    config: WorkforceForecastConfig,
) -> pd.DataFrame:
    """Prepare chronological training data."""

    required = {
        "date",
        "department",
        "staff_role",
        "patient_count",
    }

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    features, target = generate_feature_matrix(
        frame,
        lags=(1, 7),
        rolling_windows=(3, 7),
    )

    if features.empty:
        raise ValueError(
            "No usable workforce training rows "
            "remain after feature generation."
        )

    max_history = 7

    ordered = frame.sort_values(
        [
            "department",
            "staff_role",
            "date",
        ]
    ).reset_index(drop=True)

    usable_dates: list[pd.Timestamp] = []

    for _, group in ordered.groupby(
        [
            "department",
            "staff_role",
        ],
        sort=False,
    ):
        usable = group.iloc[
            max_history:
        ]

        usable_dates.extend(
            usable["date"].tolist()
        )

    if len(usable_dates) != len(features):
        raise ValueError(
            "Feature and target alignment failed."
        )

    training_frame = features.copy()

    training_frame["date"] = pd.to_datetime(
        usable_dates,
        utc=True,
    )

    training_frame["target"] = (
        target.to_numpy(dtype=float)
    )

    return training_frame


def train_workforce_forecaster(
    frame: pd.DataFrame,
    config: WorkforceForecastConfig = DEFAULT_CONFIG,
) -> WorkforceTrainingResult:
    """Train the workforce forecasting model."""

    training_frame = _prepare_training_frame(
        frame,
        config,
    )

    if (
        len(training_frame)
        < config.min_history_points
    ):
        raise ValueError(
            "Insufficient workforce history for "
            "training. "
            f"At least {config.min_history_points} "
            "usable observations are required."
        )

    training_frame = training_frame.sort_values(
        "date"
    ).reset_index(drop=True)

    split_index = max(
        1,
        min(
            len(training_frame) - 1,
            int(
                len(training_frame)
                * 0.8
            ),
        ),
    )

    train_frame = training_frame.iloc[
        :split_index
    ].copy()

    validation_frame = training_frame.iloc[
        split_index:
    ].copy()

    feature_columns = tuple(
        column
        for column in training_frame.columns
        if column not in {
            "date",
            "target",
        }
    )

    train_data = xgb.DMatrix(
        train_frame[
            list(feature_columns)
        ],
        label=train_frame["target"],
        feature_names=list(
            feature_columns
        ),
    )

    validation_data = xgb.DMatrix(
        validation_frame[
            list(feature_columns)
        ],
        label=validation_frame["target"],
        feature_names=list(
            feature_columns
        ),
    )

    parameters = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "seed": config.random_seed,
        "nthread": 1,
    }

    model = xgb.train(
        params=parameters,
        dtrain=train_data,
        num_boost_round=100,
        evals=[
            (
                train_data,
                "train",
            ),
            (
                validation_data,
                "validation",
            ),
        ],
        verbose_eval=False,
    )

    validation_predictions = np.maximum(
        model.predict(validation_data),
        0.0,
    )

    actual = validation_frame[
        "target"
    ].to_numpy(dtype=float)

    metrics = _calculate_metrics(
        actual,
        validation_predictions,
    )

    residuals = (
        actual
        - validation_predictions
    )

    residual_std = float(
        np.std(
            residuals,
            ddof=1,
        )
    ) if len(residuals) > 1 else 0.0

    confidence = float(
        np.clip(
            1.0 - (
                metrics["rmse"]
                / max(
                    np.mean(
                        np.abs(actual)
                    ),
                    1e-8,
                )
            ),
            0.05,
            0.99,
        )
    )

    return WorkforceTrainingResult(
        model=model,
        feature_columns=feature_columns,
        metrics=metrics,
        residual_std=residual_std,
        confidence=confidence,
    )