"""Data preparation and validation for inventory simulation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def validate_demand(
    demand: Sequence[float],
) -> list[float]:
    """Validate predicted demand values."""

    if not demand:
        raise ValueError(
            "Predicted demand cannot be empty."
        )

    values = [
        float(value)
        for value in demand
    ]

    if not all(
        np.isfinite(value)
        for value in values
    ):
        raise ValueError(
            "Predicted demand must contain "
            "finite values."
        )

    if any(
        value < 0
        for value in values
    ):
        raise ValueError(
            "Predicted demand cannot be negative."
        )

    return values


def normalize_incoming(
    incoming: Sequence[float],
    horizon: int,
) -> list[float]:
    """Normalize incoming stock to the simulation horizon."""

    if any(
        float(value) < 0
        for value in incoming
    ):
        raise ValueError(
            "Expected incoming stock cannot be negative."
        )

    normalized = [
        float(value)
        for value in incoming[:horizon]
    ]

    if len(normalized) < horizon:
        normalized.extend(
            [0.0] * (
                horizon - len(normalized)
            )
        )

    return normalized