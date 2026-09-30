"""Evaluation utilities for explanation consistency."""

from __future__ import annotations

import numpy as np

from .features import calculate_attributions


def evaluate_explanations(
    features: dict[str, float],
    prediction: float,
    baseline: float,
) -> dict[str, float]:
    """Evaluate attribution completeness against the prediction delta."""
    contributions = calculate_attributions(
        features,
        baseline=baseline,
    )

    contribution_sum = sum(
        float(item["contribution"])
        for item in contributions
    )

    target_delta = float(prediction) - float(baseline)

    return {
        "attribution_sum": contribution_sum,
        "target_delta": target_delta,
        "completeness_error": float(
            abs(contribution_sum - target_delta)
        ),
        "is_complete": float(
            np.isclose(
                contribution_sum,
                target_delta,
            )
        ),
    }