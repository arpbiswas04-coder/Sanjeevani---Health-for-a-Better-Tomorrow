"""Evaluation helpers for inventory simulation."""

from __future__ import annotations

import numpy as np

from ai.common.metrics import (
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    calculate_wape,
)


def evaluate_projection(
    actual_stock: list[float],
    projected_stock: list[float],
) -> dict[str, float]:
    """Evaluate projected inventory against observed inventory."""

    if len(actual_stock) != len(projected_stock):
        raise ValueError(
            "actual_stock and projected_stock "
            "must have the same length."
        )

    if not actual_stock:
        raise ValueError(
            "At least one stock observation is required."
        )

    actual = np.asarray(
        actual_stock,
        dtype=float,
    )

    projected = np.asarray(
        projected_stock,
        dtype=float,
    )

    return {
        "mae": calculate_mae(
            actual,
            projected,
        ),
        "rmse": calculate_rmse(
            actual,
            projected,
        ),
        "mape": calculate_mape(
            actual,
            projected,
        ),
        "wape": calculate_wape(
            actual,
            projected,
        ),
    }