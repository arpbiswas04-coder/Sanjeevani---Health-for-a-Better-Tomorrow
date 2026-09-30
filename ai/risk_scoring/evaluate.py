"""Evaluation utilities for composite risk scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DEFAULT_CONFIG
from .features import build_risk_features
from .train import CompositeRiskScorer


def evaluate_risk_scores(
    frame: pd.DataFrame,
    scorer: CompositeRiskScorer | None = None,
) -> dict[str, float]:
    """Evaluate score stability and coverage on supplied indicators."""
    features = build_risk_features(frame)

    if scorer is None:
        scorer = CompositeRiskScorer()

    scores = [
        scorer.calculate_score(row.to_dict())["risk_score"]
        for _, row in features.iterrows()
    ]

    values = np.asarray(scores, dtype=float)

    if values.size == 0:
        raise ValueError("At least one record is required")

    return {
        "mean_risk_score": float(values.mean()),
        "min_risk_score": float(values.min()),
        "max_risk_score": float(values.max()),
        "coverage_ratio": float(
            len(values) / max(len(frame), 1)
        ),
    }