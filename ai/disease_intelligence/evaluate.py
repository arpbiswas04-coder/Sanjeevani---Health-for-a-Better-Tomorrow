"""Evaluation utilities for disease intelligence."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai.common.metrics import (
    calculate_mae,
    calculate_rmse,
)
from ai.disease_intelligence.config import (
    DEFAULT_CONFIG,
    DiseaseIntelligenceConfig,
)
from ai.disease_intelligence.features import (
    build_disease_features,
)
from ai.disease_intelligence.train import (
    DiseaseTrainingResult,
    calculate_surge_probability,
)


def evaluate_disease_intelligence(
    frame: pd.DataFrame,
    training_result: DiseaseTrainingResult,
    config: DiseaseIntelligenceConfig = DEFAULT_CONFIG,
) -> dict[str, float]:
    """Evaluate rolling-baseline disease intelligence."""

    features = build_disease_features(
        frame,
        growth_window=config.growth_window,
    )

    usable = features.dropna(
        subset=["rolling_mean"]
    )

    if usable.empty:
        raise ValueError(
            "No usable evaluation samples"
        )

    actual = usable["case_count"].to_numpy(
        dtype=float
    )

    expected = usable[
        "rolling_mean"
    ].to_numpy(dtype=float)

    probabilities = np.array(
        [
            calculate_surge_probability(
                float(growth),
                float(anomaly),
                config,
            )
            for growth, anomaly in zip(
                usable["growth_rate"],
                usable["anomaly_score"],
            )
        ],
        dtype=float,
    )

    return {
        "mae": float(
            calculate_mae(
                actual,
                expected,
            )
        ),
        "rmse": float(
            calculate_rmse(
                actual,
                expected,
            )
        ),
        "mean_surge_probability": float(
            np.mean(probabilities)
        ),
        "confidence": float(
            training_result.confidence
        ),
    }