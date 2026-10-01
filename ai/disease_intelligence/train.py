"""Training and calibration utilities for disease intelligence."""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class DiseaseTrainingResult:
    """Calibrated disease-intelligence model."""

    metrics: dict[str, float]
    confidence: float
    baseline_mean: float
    baseline_std: float
    model_version: str = (
        "disease-intelligence-hybrid-v1"
    )


def _surge_probability(
    growth_rate: float,
    anomaly_score: float,
    config: DiseaseIntelligenceConfig,
) -> float:
    """Combine growth and anomaly evidence."""

    growth_signal = min(
        max(growth_rate, 0.0),
        2.0,
    ) / 2.0

    anomaly_signal = min(
        max(anomaly_score, 0.0),
        4.0,
    ) / 4.0

    threshold_signal = float(
        anomaly_score >= config.z_threshold
    )

    probability = (
        0.45 * growth_signal
        + 0.35 * anomaly_signal
        + 0.20 * threshold_signal
    )

    return float(
        np.clip(
            probability,
            0.0,
            1.0,
        )
    )


def calculate_surge_probability(
    growth_rate: float,
    anomaly_score: float,
    config: DiseaseIntelligenceConfig = DEFAULT_CONFIG,
) -> float:
    """Public surge-probability calculation."""

    return _surge_probability(
        growth_rate,
        anomaly_score,
        config,
    )


def train_disease_intelligence(
    frame: pd.DataFrame,
    config: DiseaseIntelligenceConfig = DEFAULT_CONFIG,
) -> DiseaseTrainingResult:
    """Calibrate the hybrid outbreak early-warning system."""

    if len(frame) < config.min_history_points:
        raise ValueError(
            "Insufficient history for disease intelligence"
        )

    features = build_disease_features(
        frame,
        growth_window=config.growth_window,
    )

    usable = features.dropna(
        subset=[
            "rolling_mean",
            "growth_rate",
        ]
    )

    if usable.empty:
        raise ValueError(
            "Insufficient usable history"
        )

    actual = usable["case_count"].to_numpy(
        dtype=float
    )

    expected = usable[
        "rolling_mean"
    ].to_numpy(dtype=float)

    error_mae = calculate_mae(
        actual,
        expected,
    )

    error_rmse = calculate_rmse(
        actual,
        expected,
    )

    mean_actual = max(
        float(np.mean(np.abs(actual))),
        1e-8,
    )

    relative_error = (
        error_rmse / mean_actual
    )

    confidence = float(
        np.clip(
            1.0 - relative_error,
            0.05,
            0.99,
        )
    )

    return DiseaseTrainingResult(
        metrics={
            "mae": float(error_mae),
            "rmse": float(error_rmse),
        },
        confidence=confidence,
        baseline_mean=float(
            usable["rolling_mean"].mean()
        ),
        baseline_std=float(
            usable["rolling_std"].mean()
        ),
    )