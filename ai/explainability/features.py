"""SHAP-based feature attribution utilities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import shap

from .data import validate_features


def calculate_attributions(
    features: Mapping[str, float],
    baseline: float = 0.0,
    *,
    model: Any | None = None,
) -> list[dict[str, float | str]]:
    """Calculate feature contributions using SHAP when a model is supplied.

    A model-backed explanation uses SHAP TreeExplainer for tree models.
    When no model is supplied, a deterministic baseline-relative fallback
    is retained so the existing lightweight API remains usable.
    """

    normalized = validate_features(features)

    if model is None:
        return _calculate_baseline_attributions(
            normalized,
            baseline,
        )

    return _calculate_shap_attributions(
        normalized,
        model,
        baseline,
    )


def _calculate_shap_attributions(
    features: Mapping[str, float],
    model: Any,
    baseline: float,
) -> list[dict[str, float | str]]:
    """Calculate SHAP TreeExplainer attributions."""

    feature_names = list(features.keys())

    values = np.asarray(
        [[features[name] for name in feature_names]],
        dtype=float,
    )

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(values)

    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    contribution_values = np.asarray(
        shap_values,
        dtype=float,
    )

    if contribution_values.ndim == 2:
        contribution_values = (
            contribution_values[0]
        )

    if contribution_values.ndim != 1:
        raise ValueError(
            "SHAP output has an unsupported shape."
        )

    if len(contribution_values) != len(
        feature_names
    ):
        raise ValueError(
            "Number of SHAP contributions does not "
            "match the number of features."
        )

    contributions: list[
        dict[str, float | str]
    ] = []

    for index, name in enumerate(feature_names):
        contribution = float(
            contribution_values[index]
        )

        if contribution > 0:
            direction = "positive"
        elif contribution < 0:
            direction = "negative"
        else:
            direction = "neutral"

        contributions.append(
            {
                "feature": name,
                "value": float(features[name]),
                "contribution": contribution,
                "direction": direction,
            }
        )

    return contributions


def _calculate_baseline_attributions(
    features: Mapping[str, float],
    baseline: float,
) -> list[dict[str, float | str]]:
    """Calculate deterministic fallback attributions."""

    total = sum(
        abs(value)
        for value in features.values()
    )

    if total == 0.0:
        return [
            {
                "feature": name,
                "value": float(value),
                "contribution": 0.0,
                "direction": "neutral",
            }
            for name, value in features.items()
        ]

    total_value = sum(
        features.values()
    )

    contributions: list[
        dict[str, float | str]
    ] = []

    for name, value in features.items():
        contribution = (
            (value / total)
            * (total_value - baseline)
        )

        if contribution > 0:
            direction = "positive"
        elif contribution < 0:
            direction = "negative"
        else:
            direction = "neutral"

        contributions.append(
            {
                "feature": name,
                "value": float(value),
                "contribution": float(
                    contribution
                ),
                "direction": direction,
            }
        )

    return contributions