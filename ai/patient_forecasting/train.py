"""
Sanjeevani Grid - Patient Forecasting Model Training
ai/patient_forecasting/train.py

Implements XGBoost regression for patient-footfall forecasting.
Uses chronological validation, real holdout metrics, and
versioned model artifacts.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xgboost as xgb

from ai.common.base_model import BaseForecaster
from ai.common.metrics import calculate_forecasting_metrics
from ai.patient_forecasting.config import (
    DEFAULT_CONFIG,
)
from ai.patient_forecasting.data import (
    chronological_train_test_split,
    validate_and_load_series,
)
from ai.patient_forecasting.features import (
    generate_feature_matrix,
)


# Implementation defaults.
# The project specification permits XGBoost but does not prescribe
# exact hyperparameters for patient forecasting.
DEFAULT_XGBOOST_PARAMS: Dict[str, Any] = {
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "seed": DEFAULT_CONFIG.random_seed,
}

DEFAULT_NUM_BOOST_ROUND = 60
DEFAULT_MODEL_VERSION = "patient-xgboost-v1"


class XGBoostPatientForecaster(BaseForecaster):
    """
    XGBoost patient-footfall forecaster.

    Uses chronological validation so future observations are not
    used during model training.
    """

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        model_version: str = DEFAULT_MODEL_VERSION,
        feature_names: Optional[List[str]] = None,
        lags: Optional[List[int]] = None,
        windows: Optional[List[int]] = None,
    ) -> None:

        super().__init__(
            model_name="XGBoostPatientForecaster"
        )

        self.params = dict(
            params or DEFAULT_XGBOOST_PARAMS
        )

        self.num_boost_round = DEFAULT_NUM_BOOST_ROUND

        if "n_estimators" in self.params:
            self.num_boost_round = int(
                self.params.pop("n_estimators")
            )

        if "random_state" in self.params:
            self.params["seed"] = self.params.pop(
                "random_state"
            )

        self.model_version = model_version
        self.feature_names = feature_names or []

        self.lags = (
            lags
            if lags is not None
            else list(DEFAULT_CONFIG.lags)
        )

        self.windows = (
            windows
            if windows is not None
            else list(DEFAULT_CONFIG.rolling_windows)
        )

        self.booster: Optional[xgb.Booster] = None

        self.validation_metrics: Dict[str, float] = {}

        self.residual_std: float = 0.0

        self.confidence: float = 0.0

    def fit(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[
            np.ndarray,
            pd.Series,
            List[float],
        ],
        X_val: Optional[
            Union[np.ndarray, pd.DataFrame]
        ] = None,
        y_val: Optional[
            Union[
                np.ndarray,
                pd.Series,
                List[float],
            ]
        ] = None,
        num_boost_round: Optional[int] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> "XGBoostPatientForecaster":
        """
        Fit the XGBoost model and calculate validation metrics.
        """

        actual_rounds = (
            num_boost_round
            or self.num_boost_round
        )

        # Convert training features.
        if isinstance(X, pd.DataFrame):

            self.feature_names = list(X.columns)

            X_arr = X.values.astype(
                np.float32
            )

        else:

            X_arr = np.asarray(
                X,
                dtype=np.float32,
            )

            if not self.feature_names:
                self.feature_names = [
                    f"f{i}"
                    for i in range(X_arr.shape[1])
                ]

        y_arr = np.asarray(
            y,
            dtype=np.float32,
        ).ravel()

        if len(X_arr) != len(y_arr):
            raise ValueError(
                "Training feature and target lengths "
                "must match."
            )

        dtrain = xgb.DMatrix(
            X_arr,
            label=y_arr,
            feature_names=self.feature_names,
        )

        evals = [
            (dtrain, "train")
        ]

        dval = None
        y_val_arr = None

        # Optional chronological validation set.
        if X_val is not None and y_val is not None:

            if isinstance(X_val, pd.DataFrame):

                X_val_arr = (
                    X_val[self.feature_names]
                    .values
                    .astype(np.float32)
                )

            else:

                X_val_arr = np.asarray(
                    X_val,
                    dtype=np.float32,
                )

            y_val_arr = np.asarray(
                y_val,
                dtype=np.float32,
            ).ravel()

            if len(X_val_arr) != len(
                y_val_arr
            ):
                raise ValueError(
                    "Validation feature and target "
                    "lengths must match."
                )

            dval = xgb.DMatrix(
                X_val_arr,
                label=y_val_arr,
                feature_names=self.feature_names,
            )

            evals.append(
                (dval, "val")
            )

        # Train native XGBoost booster.
        self.booster = xgb.train(
            params=self.params,
            dtrain=dtrain,
            num_boost_round=actual_rounds,
            evals=evals
            if len(evals) > 1
            else None,
            verbose_eval=verbose,
        )

        self.is_fitted = True

        # Prefer holdout validation metrics whenever
        # a validation set is supplied.
        if dval is not None and y_val_arr is not None:

            predictions = self.booster.predict(
                dval
            )

            predictions = np.maximum(
                0.0,
                predictions,
            )

            self.validation_metrics = (
                calculate_forecasting_metrics(
                    y_val_arr,
                    predictions,
                )
            )

            residuals = (
                y_val_arr - predictions
            )

        else:

            predictions = self.booster.predict(
                dtrain
            )

            predictions = np.maximum(
                0.0,
                predictions,
            )

            self.validation_metrics = (
                calculate_forecasting_metrics(
                    y_arr,
                    predictions,
                )
            )

            residuals = (
                y_arr - predictions
            )

        # Empirical residual spread.
        self.residual_std = float(
            np.std(residuals)
        )

        # Confidence is derived from measured
        # validation error rather than being fabricated.
        actual_values = (
            y_val_arr
            if y_val_arr is not None
            else y_arr
        )

        mean_actual = float(
            np.mean(actual_values)
        )

        norm_rmse = (
            self.validation_metrics["rmse"]
            / (mean_actual + 1e-6)
        )

        self.confidence = float(
            np.clip(
                1.0 / (1.0 + norm_rmse),
                0.05,
                0.99,
            )
        )

        return self

    def predict(
        self,
        X: Union[
            np.ndarray,
            pd.DataFrame,
        ],
        **kwargs: Any,
    ) -> np.ndarray:
        """
        Generate non-negative patient-footfall forecasts.
        """

        if (
            not self.is_fitted
            or self.booster is None
        ):
            raise RuntimeError(
                "XGBoostPatientForecaster must be "
                "fitted before predict."
            )

        if isinstance(X, pd.DataFrame):

            X_arr = (
                X[self.feature_names]
                .values
                .astype(np.float32)
            )

        else:

            X_arr = np.asarray(
                X,
                dtype=np.float32,
            )

        dmatrix = xgb.DMatrix(
            X_arr,
            feature_names=self.feature_names,
        )

        raw_predictions = (
            self.booster.predict(
                dmatrix
            )
        )

        return np.maximum(
            0.0,
            raw_predictions,
        )


def train_patient_pipeline(
    records: Any,
    test_size: Union[int, float] = 7,
    model_version: str = DEFAULT_MODEL_VERSION,
    params: Optional[Dict[str, Any]] = None,
    save_path: Optional[
        Union[str, Path]
    ] = None,
) -> Tuple[
    XGBoostPatientForecaster,
    Dict[str, float],
]:
    """
    End-to-end patient-footfall training pipeline.

    Steps:
    1. Validate and load historical visits.
    2. Generate deterministic features.
    3. Split chronologically.
    4. Train XGBoost.
    5. Calculate holdout metrics.
    6. Optionally save the trained artifact.
    """

    df_clean = (
        validate_and_load_series(
            records
        )
    )

    feat_df, feature_cols = (
        generate_feature_matrix(
            df_clean,
            target_col="visits",
        )
    )

    if len(feat_df) < 4:
        raise ValueError(
            "Insufficient feature rows after "
            "feature generation for training."
        )

    train_df, test_df = (
        chronological_train_test_split(
            feat_df,
            test_size=test_size,
        )
    )

    X_train = train_df[
        feature_cols
    ]

    y_train = train_df[
        "visits"
    ].values

    X_test = test_df[
        feature_cols
    ]

    y_test = test_df[
        "visits"
    ].values

    forecaster = (
        XGBoostPatientForecaster(
            params=params,
            model_version=model_version,
            feature_names=feature_cols,
        )
    )

    forecaster.fit(
        X_train,
        y_train,
        X_val=X_test,
        y_val=y_test,
    )

    if save_path:
        forecaster.save(
            save_path
        )

    return (
        forecaster,
        forecaster.validation_metrics,
    )


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {
        "module": "patient_forecasting.train",
        "status": "placeholder",
    }