"""Feature attribution utilities."""

from __future__ import annotations

from collections.abc import Mapping

from .data import validate_features


def calculate_attributions(
    features: Mapping[str, float],
    baseline: float = 0.0,
) -> list[dict[str, float | str]]:
    """
    Calculate deterministic baseline-relative feature contributions.

    This is a transparent fallback attribution method. It is not SHAP/LIME.
    """
    normalized = validate_features(features)

    total = sum(abs(value) for value in normalized.values())

    if total == 0.0:
        return [
            {
                "feature": name,
                "value": value,
                "contribution": 0.0,
                "direction": "neutral",
            }
            for name, value in normalized.items()
        ]

    contributions = []

    for name, value in normalized.items():
        contribution = (
            (value / total) * (sum(normalized.values()) - baseline)
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
                "value": value,
                "contribution": float(contribution),
                "direction": direction,
            }
        )

    return contributions