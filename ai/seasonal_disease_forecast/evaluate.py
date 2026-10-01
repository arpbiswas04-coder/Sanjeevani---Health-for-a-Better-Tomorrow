"""Evaluation utilities for seasonal disease forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd

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
from .features import (
    create_features,
    get_feature_columns,
)
from .train import SeasonalDiseaseModel


def evaluate_model(
    model_bundle: SeasonalDiseaseModel,
    frame: pd.DataFrame,
    *,
    config: SeasonalDiseaseForecastConfig = DEFAULT_CONFIG,
) -> dict[str, float]:
    """Evaluate a trained model on the supplied time-series data."""

    features = create_features(
        frame,
        lags=config.lags,
        rolling_windows=config.rolling_windows,
    )

    if features.empty:
        raise ValueError(
            "Insufficient data after feature engineering."
        )

    feature_columns = get_feature_columns(
        features
    )

    actual = features[
        "case_count"
    ].to_numpy(dtype=float)

    predicted = np.maximum(
        model_bundle.model.predict(
            features[feature_columns]
        ),
        0.0,
    )

    return {
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


def calculate_seasonal_signal(
    frame: pd.DataFrame,
) -> float:
    """Estimate the strength of recurring monthly seasonality.

    The value is derived from the coefficient of variation
    of monthly mean case counts. It is a descriptive signal,
    not a probability.
    """

    if "case_count" not in frame.columns:
        raise ValueError(
            "Input frame must contain case_count."
        )

    if frame.empty:
        raise ValueError(
            "Input frame cannot be empty."
        )

    monthly = (
        frame["case_count"]
        .groupby(frame.index.month)
        .mean()
    )

    if len(monthly) < 2:
        return 0.0

    mean_value = float(
        monthly.mean()
    )

    if mean_value == 0.0:
        return 0.0

    signal = float(
        monthly.std(ddof=0)
        / mean_value
    )

    return max(0.0, signal)