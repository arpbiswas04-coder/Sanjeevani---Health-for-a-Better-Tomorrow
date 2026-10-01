"""
Sanjeevani Grid - Anomaly Detection Features
ai/anomaly_detection/features.py

Computes robust statistical features and z-scores using Median Absolute Deviation (MAD)
for clinical, inventory, and operational metrics without data leakage.
"""

from typing import Any, Dict, List, Mapping, Sequence

import numpy as np

from ai.anomaly_detection.config import (
    DEFAULT_Z_THRESHOLD,
    EPSILON,
    MAD_NORMAL_SCALE,
)


def compute_robust_zscore(
    current_value: float,
    history: Sequence[float],
    z_threshold: float = DEFAULT_Z_THRESHOLD,
    epsilon: float = EPSILON,
) -> Dict[str, Any]:
    """
    Compute robust z-score using Median Absolute Deviation (MAD).

    Parameters
    ----------
    current_value : float
        The observed value to evaluate.
    history : Sequence[float]
        Historical sequence representing normal operational baseline.
    z_threshold : float, default 3.0
        Cutoff threshold for anomaly classification.
    epsilon : float, default 1e-8
        Numerical tolerance to prevent division by zero.

    Returns
    -------
    dict
        Dictionary containing z_score, baseline_median, baseline_mad,
        is_anomaly, direction, and diagnostics.
    """
    if len(history) < 3:
        raise ValueError(f"History must contain at least 3 points; got {len(history)}")

    arr = np.asarray(history, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("History contains non-finite values (NaN or Inf).")

    val = float(current_value)
    if not np.isfinite(val):
        raise ValueError("current_value must be finite.")

    median = float(np.median(arr))
    abs_deviations = np.abs(arr - median)
    mad = float(np.median(abs_deviations))
    scaled_mad = mad * MAD_NORMAL_SCALE

    diff = val - median

    # Safe division handling zero/near-zero variance
    if scaled_mad > epsilon:
        z_score = diff / scaled_mad
    else:
        # Zero variance history (e.g. [10, 10, 10, 10])
        if abs(diff) <= epsilon:
            z_score = 0.0
        else:
            # Significant departure from perfectly uniform baseline
            # Assign deterministic score proportional to absolute deviation
            sign = 1.0 if diff > 0 else -1.0
            z_score = sign * max(z_threshold + 0.5, abs(diff) / max(1.0, abs(median)))

    abs_z = abs(z_score)
    is_anomaly = bool(abs_z >= z_threshold)

    # Direction determination
    if z_score >= 1.0:
        direction = "surge"
    elif z_score <= -1.0:
        direction = "drop"
    else:
        direction = "normal"

    return {
        "current_value": val,
        "baseline_median": round(median, 4),
        "baseline_mad": round(mad, 4),
        "z_score": round(float(z_score), 4),
        "abs_z_score": round(float(abs_z), 4),
        "is_anomaly": is_anomaly,
        "direction": direction,
        "sample_size": len(arr),
    }


def build_anomaly_features(values: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Derive anomaly detection features from request payload mapping.
    """
    current_value = float(values["current_value"])
    history = list(values["history"])
    z_threshold = float(values.get("z_threshold", DEFAULT_Z_THRESHOLD))

    return compute_robust_zscore(
        current_value=current_value,
        history=history,
        z_threshold=z_threshold,
    )


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.features", "status": "placeholder"}
