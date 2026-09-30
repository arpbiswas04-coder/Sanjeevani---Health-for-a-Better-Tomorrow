"""
Sanjeevani Grid - Anomaly Detection Evaluation Utilities
ai/anomaly_detection/evaluate.py

Computes genuine classification metrics (accuracy, precision, recall, f1)
for anomaly detection evaluations against ground-truth anomaly flags.

Reuses `ai.common.metrics.calculate_classification_metrics`.
"""

from typing import Any, Dict, Sequence

from ai.common.metrics import calculate_classification_metrics
from ai.anomaly_detection.features import compute_robust_zscore


def evaluate_anomaly_predictions(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> Dict[str, float]:
    """
    Evaluate predicted binary anomaly flags against ground-truth labels.

    Parameters
    ----------
    y_true : Sequence[int]
        Ground-truth labels (1 = anomaly, 0 = normal).
    y_pred : Sequence[int]
        Predicted anomaly flags (1 = anomaly, 0 = normal).

    Returns
    -------
    dict[str, float]
        Classification metrics dictionary.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Length mismatch: {len(y_true)} ground-truth labels vs {len(y_pred)} predictions."
        )

    return calculate_classification_metrics(y_true, y_pred)


def evaluate_records_anomaly(
    records: Sequence[Dict[str, Any]],
    y_true: Sequence[int],
) -> Dict[str, float]:
    """
    Evaluate a sequence of record dicts (each having current_value and history)
    against ground-truth anomaly labels.
    """
    if len(records) != len(y_true):
        raise ValueError(
            f"Length mismatch: {len(records)} records vs {len(y_true)} ground-truth labels."
        )

    y_pred = []
    for r in records:
        res = compute_robust_zscore(
            current_value=float(r["current_value"]),
            history=r["history"],
            z_threshold=float(r.get("z_threshold", 3.0)),
        )
        y_pred.append(int(res["is_anomaly"]))

    return calculate_classification_metrics(y_true, y_pred)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.evaluate", "status": "placeholder"}
