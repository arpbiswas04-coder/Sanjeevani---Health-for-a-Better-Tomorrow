"""
Sanjeevani Grid - Expiry Prediction Evaluation Utilities
ai/expiry_prediction/evaluate.py

Computes genuine classification and evaluation metrics for batch expiration
predictions against ground-truth spoilage outcomes.

Reuses `ai.common.metrics.calculate_classification_metrics`.
"""

from typing import Any, Dict, Sequence

from ai.common.metrics import calculate_classification_metrics
from ai.expiry_prediction.data import validate_and_load_expiry_records
from ai.expiry_prediction.features import build_expiry_features


def evaluate_expiry_predictions(
    records: Any,
    y_true: Sequence[int],
    wastage_threshold: float = 0.0,
) -> Dict[str, float]:
    """
    Evaluate batch spoilage predictions against binary ground-truth outcomes.

    Parameters
    ----------
    records : DataFrame or Iterable[dict]
        Batch records to evaluate.
    y_true : Sequence[int]
        Binary ground-truth labels (1 = batch suffered spoilage/wastage, 0 = no wastage).
    wastage_threshold : float, default 0.0
        Minimum likely_unused_quantity to flag as positive wastage prediction.

    Returns
    -------
    dict[str, float]
        Classification metrics: accuracy, precision, recall, f1, and confusion matrix counts.

    Raises
    ------
    ValueError
        If length of y_true does not match records.
    """
    frame = validate_and_load_expiry_records(records)
    if len(frame) != len(y_true):
        raise ValueError(
            f"Length mismatch: {len(frame)} records vs {len(y_true)} ground-truth labels."
        )

    rows = frame.to_dict(orient="records")
    y_pred = [
        int(build_expiry_features(r)["likely_unused_quantity"] > wastage_threshold)
        for r in rows
    ]

    return calculate_classification_metrics(y_true, y_pred)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.evaluate", "status": "placeholder"}
