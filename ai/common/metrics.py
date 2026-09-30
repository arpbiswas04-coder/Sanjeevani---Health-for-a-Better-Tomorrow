"""
Sanjeevani Grid - Evaluation Metrics
ai/common/metrics.py

Provides rigorous, mathematically verified evaluation metrics for time-series forecasting,
risk scoring, and classification pipelines. Fabricated or hardcoded metrics are forbidden.
"""

import math
from typing import Dict, Sequence, Union
import numpy as np


def _validate_paired_inputs(
    y_true: Sequence[Union[int, float]],
    y_pred: Sequence[Union[int, float]],
) -> tuple[np.ndarray, np.ndarray]:
    """Validate paired ground-truth and prediction sequences."""
    if len(y_true) == 0:
        raise ValueError("Cannot calculate metrics on empty ground-truth sequence.")
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Length mismatch: y_true has {len(y_true)} items, y_pred has {len(y_pred)} items."
        )

    arr_true = np.asarray(y_true, dtype=np.float64)
    arr_pred = np.asarray(y_pred, dtype=np.float64)

    if not np.all(np.isfinite(arr_true)):
        raise ValueError("Ground-truth array contains non-finite values (NaN or Inf).")
    if not np.all(np.isfinite(arr_pred)):
        raise ValueError("Prediction array contains non-finite values (NaN or Inf).")

    return arr_true, arr_pred


def calculate_mae(
    y_true: Sequence[Union[int, float]],
    y_pred: Sequence[Union[int, float]],
) -> float:
    """Mean Absolute Error (MAE): (1/n) * sum(|y_true - y_pred|)."""
    arr_true, arr_pred = _validate_paired_inputs(y_true, y_pred)
    return float(np.mean(np.abs(arr_true - arr_pred)))


def calculate_rmse(
    y_true: Sequence[Union[int, float]],
    y_pred: Sequence[Union[int, float]],
) -> float:
    """Root Mean Squared Error (RMSE): sqrt((1/n) * sum((y_true - y_pred)^2))."""
    arr_true, arr_pred = _validate_paired_inputs(y_true, y_pred)
    return float(np.sqrt(np.mean((arr_true - arr_pred) ** 2)))


def calculate_mape(
    y_true: Sequence[Union[int, float]],
    y_pred: Sequence[Union[int, float]],
    epsilon: float = 1e-8,
) -> float:
    """
    Mean Absolute Percentage Error (MAPE) in percentage (0 - 100+).
    Uses epsilon in denominator to safely handle division by zero.
    """
    arr_true, arr_pred = _validate_paired_inputs(y_true, y_pred)
    denom = np.maximum(np.abs(arr_true), epsilon)
    return float(np.mean(np.abs((arr_true - arr_pred) / denom)) * 100.0)


def calculate_wape(
    y_true: Sequence[Union[int, float]],
    y_pred: Sequence[Union[int, float]],
) -> float:
    """
    Weighted Absolute Percentage Error (WAPE) in percentage:
    (sum(|y_true - y_pred|) / sum(|y_true|)) * 100.0.
    Handles all-zero actuals safely.
    """
    arr_true, arr_pred = _validate_paired_inputs(y_true, y_pred)
    sum_abs_err = np.sum(np.abs(arr_true - arr_pred))
    sum_actual = np.sum(np.abs(arr_true))

    if sum_actual == 0.0:
        return 0.0 if sum_abs_err == 0.0 else 100.0
    return float((sum_abs_err / sum_actual) * 100.0)


def calculate_forecasting_metrics(
    y_true: Sequence[Union[int, float]],
    y_pred: Sequence[Union[int, float]],
) -> Dict[str, float]:
    """Calculate standard suite of time-series forecasting metrics."""
    return {
        "mae": calculate_mae(y_true, y_pred),
        "rmse": calculate_rmse(y_true, y_pred),
        "mape": calculate_mape(y_true, y_pred),
        "wape": calculate_wape(y_true, y_pred),
    }


def calculate_brier_score(
    y_true: Sequence[Union[int, float]],
    y_prob: Sequence[Union[int, float]],
) -> float:
    """
    Brier Score for probabilistic binary forecasts: (1/n) * sum((y_prob - y_true)^2).
    Validates that probabilities are bounded in [0, 1].
    """
    arr_true, arr_prob = _validate_paired_inputs(y_true, y_prob)
    if np.any((arr_prob < 0.0) | (arr_prob > 1.0)):
        raise ValueError("Probabilities in y_prob must be bounded between 0.0 and 1.0.")
    if not np.all(np.isin(arr_true, [0, 1])):
        raise ValueError("Ground-truth in y_true for Brier score must be binary labels (0 or 1).")

    return float(np.mean((arr_prob - arr_true) ** 2))


def calculate_classification_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    zero_division: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate accuracy, precision, recall, and F1 score for binary classification.
    Safe handling of zero-division cases.
    """
    arr_true, arr_pred = _validate_paired_inputs(y_true, y_pred)
    if not np.all(np.isin(arr_true, [0, 1])) or not np.all(np.isin(arr_pred, [0, 1])):
        raise ValueError("Inputs to binary classification metrics must only contain 0 or 1.")

    tp = float(np.sum((arr_true == 1) & (arr_pred == 1)))
    fp = float(np.sum((arr_true == 0) & (arr_pred == 1)))
    fn = float(np.sum((arr_true == 1) & (arr_pred == 0)))
    tn = float(np.sum((arr_true == 0) & (arr_pred == 0)))

    total = len(arr_true)
    accuracy = (tp + tn) / total if total > 0 else zero_division

    precision = tp / (tp + fp) if (tp + fp) > 0 else zero_division
    recall = tp / (tp + fn) if (tp + fn) > 0 else zero_division

    if (precision + recall) > 0:
        f1 = 2.0 * (precision * recall) / (precision + recall)
    else:
        f1 = zero_division

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
    }
