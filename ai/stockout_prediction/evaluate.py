"""
Sanjeevani Grid - Stockout Prediction Evaluation Utilities
ai/stockout_prediction/evaluate.py

Computes real classification metrics by comparing the deterministic
coverage rule's predictions against a set of ground-truth stockout labels.

Metrics are delegated to ai/common/metrics.calculate_classification_metrics,
which computes genuine accuracy, precision, recall, and F1 without any
fabricated or hardcoded values.
"""

from typing import Any, Dict, Sequence

from ai.common.metrics import calculate_classification_metrics
from ai.stockout_prediction.data import validate_and_load_records
from ai.stockout_prediction.features import build_stockout_features


def evaluate_stockout_predictions(
    records: Any,
    y_true: Sequence[int],
) -> Dict[str, float]:
    """
    Evaluate the deterministic stockout rule against labelled ground truth.

    Parameters
    ----------
    records : DataFrame or Iterable[dict]
        Collection of point-in-time stockout input records.
    y_true : Sequence[int]
        Binary ground-truth labels: 1 = actual stockout occurred, 0 = did not.
        Must have the same length as records.

    Returns
    -------
    dict[str, float]
        accuracy, precision, recall, f1, plus TP / FP / TN / FN counts,
        as produced by ai/common/metrics.calculate_classification_metrics.

    Raises
    ------
    ValueError
        If y_true length does not match the number of records, or if labels
        are not binary {0, 1}.
    """
    frame = validate_and_load_records(records)

    if len(frame) != len(y_true):
        raise ValueError(
            f"y_true length ({len(y_true)}) must match the number of validated "
            f"records ({len(frame)})."
        )

    predicted = [
        int(
            build_stockout_features(row)["available_quantity"]
            < build_stockout_features(row)["demand_during_lead_time"]
        )
        for row in frame.to_dict(orient="records")
    ]

    return calculate_classification_metrics(list(y_true), predicted)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.evaluate", "status": "placeholder"}
