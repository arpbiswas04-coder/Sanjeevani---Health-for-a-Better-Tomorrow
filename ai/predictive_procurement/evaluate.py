"""Evaluation utilities for procurement demand estimation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai.common.metrics import (
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    calculate_wape,
)

from .features import estimate_daily_demand


def evaluate_model(
    frame: pd.DataFrame,
    *,
    lookback_days: int = 14,
) -> dict[str, float]:
    """Evaluate a simple rolling demand estimate."""

    values = frame[
        "quantity_consumed"
    ].astype(float).to_numpy()

    if len(values) < 3:
        raise ValueError(
            "At least three observations are required "
            "for evaluation."
        )

    actual: list[float] = []
    predicted: list[float] = []

    for index in range(1, len(values)):
        history = frame.iloc[:index]

        estimate = estimate_daily_demand(
            history,
            lookback_days=lookback_days,
        )

        actual.append(
            float(values[index])
        )

        predicted.append(
            float(estimate)
        )

    actual_array = np.asarray(
        actual,
        dtype=float,
    )

    predicted_array = np.asarray(
        predicted,
        dtype=float,
    )

    return {
        "mae": calculate_mae(
            actual_array,
            predicted_array,
        ),
        "rmse": calculate_rmse(
            actual_array,
            predicted_array,
        ),
        "mape": calculate_mape(
            actual_array,
            predicted_array,
        ),
        "wape": calculate_wape(
            actual_array,
            predicted_array,
        ),
    }