"""Training pipeline for bed occupancy forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.bed_forecasting.config import DEFAULT_CONFIG, BedForecastConfig
from ai.bed_forecasting.features import generate_feature_matrix


@dataclass(frozen=True)
class BedTrainingResult:
    """Artifacts and validation information from model training."""

    model: xgb.Booster
    feature_columns: tuple[str, ...]
    metrics: dict[str, float]
    residual_std: float
    confidence: float


def _calculate_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Calculate standard forecasting metrics."""

    errors = predicted - actual

    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))

    non_zero = np.abs(actual) > 1e-8

    if non_zero.any():
        mape = float(
            np.mean(
                np.abs(
                    (actual[non_zero] - predicted[non_zero])
                    / actual[non_zero]
                )
            )
            * 100.0
        )
    else:
        mape = 0.0

    denominator = float(np.sum(np.abs(actual)))

    if denominator > 1e-8:
        wape = float(
            np.sum(np.abs(errors)) / denominator * 100.0
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
    config: BedForecastConfig,
) -> pd.DataFrame:
    """Generate model features while preserving aligned dates."""

    required_columns = {
        "date",
        "bed_type",
        "occupancy",
    }

    missing = required_columns.difference(frame.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    features, target = generate_feature_matrix(
        frame,
        lags=config.lags,
        rolling_windows=config.rolling_windows,
    )

    max_history = max(
        (*config.lags, *config.rolling_windows),
        default=1,
    )

    ordered = (
        frame.sort_values(
            ["bed_type", "date"]
        )
        .reset_index(drop=True)
    )

    aligned_dates: list[pd.Timestamp] = []

    for _, group in ordered.groupby(
        "bed_type",
        sort=False,
    ):
        usable = group.iloc[max_history:]

        aligned_dates.extend(
            usable["date"].tolist()
        )

    if len(aligned_dates) != len(features):
        raise ValueError(
            "Feature/date alignment failed. "
            f"Generated {len(features)} feature rows but found "
            f"{len(aligned_dates)} aligned dates."
        )

    training_frame = features.copy()

    training_frame["date"] = pd.to_datetime(
        aligned_dates,
        utc=True,
    )

    training_frame["target"] = target.to_numpy(
        dtype=float
    )

    return training_frame


def train_bed_forecaster(
    frame: pd.DataFrame,
    config: BedForecastConfig = DEFAULT_CONFIG,
) -> BedTrainingResult:
    """Train a native XGBoost bed occupancy forecasting model."""

    training_frame = _prepare_training_frame(
        frame,
        config,
    )

    if len(training_frame) < config.min_history_points:
        raise ValueError(
            "Insufficient usable history for bed forecasting. "
            f"Need at least {config.min_history_points} observations "
            f"after feature generation."
        )

    # Chronological validation split.
    training_frame = training_frame.sort_values(
        "date"
    ).reset_index(drop=True)

    split_index = max(
        1,
        min(
            len(training_frame) - 1,
            int(len(training_frame) * 0.8),
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
        if column not in {"date", "target"}
    )

    train_data = xgb.DMatrix(
        train_frame[list(feature_columns)],
        label=train_frame["target"],
        feature_names=list(feature_columns),
    )

    validation_data = xgb.DMatrix(
        validation_frame[list(feature_columns)],
        label=validation_frame["target"],
        feature_names=list(feature_columns),
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
            (train_data, "train"),
            (validation_data, "validation"),
        ],
        verbose_eval=False,
    )

    validation_predictions = model.predict(
        validation_data
    )

    # Occupancy is represented as a ratio from 0 to 1.
    validation_predictions = np.clip(
        validation_predictions,
        0.0,
        1.0,
    )

    actual = validation_frame[
        "target"
    ].to_numpy(dtype=float)

    metrics = _calculate_metrics(
        actual,
        validation_predictions,
    )

    residuals = (
        actual - validation_predictions
    )

    residual_std = (
        float(np.std(residuals, ddof=1))
        if len(residuals) > 1
        else 0.0
    )

    # Confidence is derived from validation RMSE.
    # It is not a fabricated fixed value.
    confidence = float(
        np.clip(
            1.0 - metrics["rmse"],
            0.05,
            0.99,
        )
    )

    return BedTrainingResult(
        model=model,
        feature_columns=feature_columns,
        metrics=metrics,
        residual_std=residual_std,
        confidence=confidence,
    )