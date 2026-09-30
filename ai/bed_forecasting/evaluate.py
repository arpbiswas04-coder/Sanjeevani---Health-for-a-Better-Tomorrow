"""Evaluation utilities for bed occupancy forecasting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ai.bed_forecasting.config import DEFAULT_CONFIG, BedForecastConfig
from ai.bed_forecasting.features import generate_feature_matrix
from ai.bed_forecasting.train import BedTrainingResult


def evaluate_bed_forecast(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Calculate standard forecasting metrics."""

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    if actual.ndim != 1 or predicted.ndim != 1:
        raise ValueError(
            "actual and predicted must be one-dimensional arrays."
        )

    if len(actual) != len(predicted):
        raise ValueError(
            "actual and predicted must have the same length."
        )

    if len(actual) == 0:
        raise ValueError(
            "actual and predicted cannot be empty."
        )

    if not np.isfinite(actual).all():
        raise ValueError(
            "actual contains non-finite values."
        )

    if not np.isfinite(predicted).all():
        raise ValueError(
            "predicted contains non-finite values."
        )

    if (actual < 0).any() or (actual > 1).any():
        raise ValueError(
            "actual occupancy must be between 0 and 1."
        )

    if (predicted < 0).any() or (predicted > 1).any():
        raise ValueError(
            "predicted occupancy must be between 0 and 1."
        )

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
                    (actual[non_zero] - predicted[non_zero])
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


def _predict_validation_set(
    training_result: BedTrainingResult,
    validation_features: pd.DataFrame,
) -> np.ndarray:
    """Generate predictions using the trained native XGBoost model."""

    import xgboost as xgb

    matrix = xgb.DMatrix(
        validation_features[
            list(training_result.feature_columns)
        ],
        feature_names=list(
            training_result.feature_columns
        ),
    )

    predictions = training_result.model.predict(
        matrix
    )

    return np.clip(
        predictions,
        0.0,
        1.0,
    )


def backtest_bed_forecaster(
    frame: pd.DataFrame,
    training_result: BedTrainingResult,
    config: BedForecastConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """
    Evaluate a trained bed forecaster on a chronological holdout.

    The final 20% of usable observations are treated as the
    backtest period.
    """

    features, target = generate_feature_matrix(
        frame,
        lags=config.lags,
        rolling_windows=config.rolling_windows,
    )

    if len(features) < 2:
        raise ValueError(
            "At least two usable observations are required "
            "for backtesting."
        )

    ordered = (
        frame.sort_values(
            ["bed_type", "date"]
        )
        .reset_index(drop=True)
    )

    max_history = max(
        (*config.lags, *config.rolling_windows),
        default=1,
    )

    aligned_dates: list[pd.Timestamp] = []

    for _, group in ordered.groupby(
        "bed_type",
        sort=False,
    ):
        aligned_dates.extend(
            group.iloc[max_history:]["date"].tolist()
        )

    if len(aligned_dates) != len(features):
        raise ValueError(
            "Feature/date alignment failed during backtesting."
        )

    evaluation_frame = features.copy()

    evaluation_frame["date"] = pd.to_datetime(
        aligned_dates,
        utc=True,
    )

    evaluation_frame["target"] = target.to_numpy(
        dtype=float
    )

    evaluation_frame = evaluation_frame.sort_values(
        "date"
    ).reset_index(drop=True)

    split_index = max(
        1,
        min(
            len(evaluation_frame) - 1,
            int(len(evaluation_frame) * 0.8),
        ),
    )

    validation_frame = evaluation_frame.iloc[
        split_index:
    ].copy()

    predicted = _predict_validation_set(
        training_result,
        validation_frame,
    )

    actual = validation_frame[
        "target"
    ].to_numpy(dtype=float)

    metrics = evaluate_bed_forecast(
        actual,
        predicted,
    )

    return {
        "metrics": metrics,
        "samples": int(len(actual)),
        "start": validation_frame["date"].iloc[0].isoformat(),
        "end": validation_frame["date"].iloc[-1].isoformat(),
    }


def evaluate_training_result(
    training_result: BedTrainingResult,
) -> dict[str, float]:
    """Return the validation metrics stored during training."""

    return dict(training_result.metrics)