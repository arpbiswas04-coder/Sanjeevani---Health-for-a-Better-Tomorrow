"""
Sanjeevani Grid - Patient Forecasting Evaluation & Backtesting
ai/patient_forecasting/evaluate.py

Chronological holdout validation and backtesting for patient
footfall forecasting.
"""

from typing import Any, Dict, Sequence, Union

import numpy as np
import pandas as pd

from ai.common.metrics import calculate_forecasting_metrics
from ai.patient_forecasting.data import validate_and_load_series
from ai.patient_forecasting.features import generate_feature_matrix
from ai.patient_forecasting.train import XGBoostPatientForecaster


def evaluate_forecast(
    y_true: Union[
        Sequence[float],
        np.ndarray,
        pd.Series,
    ],
    y_pred: Union[
        Sequence[float],
        np.ndarray,
        pd.Series,
    ],
) -> Dict[str, float]:
    """
    Compute actual forecasting metrics.

    Metrics:
    - MAE
    - RMSE
    - MAPE
    - WAPE
    """

    y_t = np.asarray(
        y_true,
        dtype=np.float64,
    )

    y_p = np.asarray(
        y_pred,
        dtype=np.float64,
    )

    if len(y_t) != len(y_p):
        raise ValueError(
            "y_true and y_pred must have the same length."
        )

    if not np.all(np.isfinite(y_t)):
        raise ValueError(
            "y_true contains non-finite values."
        )

    if not np.all(np.isfinite(y_p)):
        raise ValueError(
            "y_pred contains non-finite values."
        )

    return calculate_forecasting_metrics(
        y_t,
        y_p,
    )


def backtest_patient_forecaster(
    forecaster: XGBoostPatientForecaster,
    df: pd.DataFrame,
    horizon_days: int = 7,
) -> Dict[str, Any]:
    """
    Evaluate a fitted patient forecaster on the final
    chronological holdout period.

    No future observations are used to construct features
    for the evaluated period.
    """

    if horizon_days <= 0:
        raise ValueError(
            "horizon_days must be positive."
        )

    if "datetime" not in df.columns:
        clean_df = validate_and_load_series(df)
    else:
        clean_df = df.copy()

    feat_df, feature_cols = (
        generate_feature_matrix(
            clean_df,
            target_col="visits",
            drop_na=True,
        )
    )

    if len(feat_df) < horizon_days:
        raise ValueError(
            f"Insufficient observations "
            f"({len(feat_df)}) for backtest horizon "
            f"({horizon_days})."
        )

    test_split = (
        feat_df
        .iloc[-horizon_days:]
        .copy()
    )

    X_test = test_split[
        feature_cols
    ]

    y_test = test_split[
        "visits"
    ].values

    y_pred = forecaster.predict(
        X_test
    )

    metrics = evaluate_forecast(
        y_test,
        y_pred,
    )

    residuals = (
        y_test - y_pred
    )

    return {
        "metrics": metrics,
        "horizon_days": horizon_days,
        "sample_size": len(y_test),
        "residual_std": float(
            np.std(residuals)
        ),
        "mean_absolute_residual": float(
            np.mean(
                np.abs(residuals)
            )
        ),
        "predictions": y_pred.tolist(),
        "ground_truth": y_test.tolist(),
    }


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {
        "module": "patient_forecasting.evaluate",
        "status": "placeholder",
    }