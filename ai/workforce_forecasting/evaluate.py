"""Evaluation utilities for workforce forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.workforce_forecasting.features import (
    generate_feature_matrix,
)
from ai.workforce_forecasting.train import (
    WorkforceTrainingResult,
)


def evaluate_workforce_forecast(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Calculate standard workforce forecasting metrics."""

    actual = np.asarray(
        actual,
        dtype=float,
    )

    predicted = np.asarray(
        predicted,
        dtype=float,
    )

    if actual.ndim != 1:
        raise ValueError(
            "actual must be a one-dimensional array."
        )

    if predicted.ndim != 1:
        raise ValueError(
            "predicted must be a one-dimensional array."
        )

    if len(actual) != len(predicted):
        raise ValueError(
            "actual and predicted must have "
            "the same length."
        )

    if len(actual) == 0:
        raise ValueError(
            "At least one observation is required."
        )

    if not (
        np.isfinite(actual).all()
        and np.isfinite(predicted).all()
    ):
        raise ValueError(
            "actual and predicted must contain "
            "only finite values."
        )

    if (actual < 0).any():
        raise ValueError(
            "actual workforce values cannot be negative."
        )

    if (predicted < 0).any():
        raise ValueError(
            "predicted workforce values cannot be negative."
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


def _prepare_validation_data(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Prepare the chronological validation portion."""

    features, target = generate_feature_matrix(
        frame,
        lags=(1, 7),
        rolling_windows=(3, 7),
    )

    if features.empty:
        raise ValueError(
            "No usable rows remain after "
            "feature generation."
        )

    split_index = max(
        1,
        min(
            len(features) - 1,
            int(len(features) * 0.8),
        ),
    )

    validation_features = features.iloc[
        split_index:
    ].copy()

    validation_target = target.iloc[
        split_index:
    ].to_numpy(dtype=float)

    return (
        validation_features,
        validation_target,
    )


def backtest_workforce_forecaster(
    frame: pd.DataFrame,
    training_result: WorkforceTrainingResult,
) -> dict[str, object]:
    """Evaluate a trained workforce model on a chronological holdout."""

    validation_features, validation_target = (
        _prepare_validation_data(frame)
    )

    aligned_features = validation_features.reindex(
        columns=training_result.feature_columns,
        fill_value=0.0,
    )

    validation_data = xgb.DMatrix(
        aligned_features,
        feature_names=list(
            training_result.feature_columns
        ),
    )

    predictions = np.maximum(
        training_result.model.predict(
            validation_data
        ),
        0.0,
    )

    metrics = evaluate_workforce_forecast(
        validation_target,
        predictions,
    )

    return {
        "metrics": metrics,
        "samples": len(validation_target),
        "actual": validation_target,
        "predicted": predictions,
    }


def evaluate_training_result(
    training_result: WorkforceTrainingResult,
) -> dict[str, float]:
    """Return metrics stored during model training."""

    return dict(
        training_result.metrics
    )