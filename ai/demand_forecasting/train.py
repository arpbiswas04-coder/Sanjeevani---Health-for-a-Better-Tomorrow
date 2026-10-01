"""
Sanjeevani Grid - Demand Forecasting Model Training
ai/demand_forecasting/train.py

Implements native XGBoost regression for medicine/equipment consumption forecasting.
Uses chronological validation, computes real holdout metrics, and serializes versioned artifacts.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import xgboost as xgb

from ai.common.base_model import BaseForecaster
from ai.common.metrics import calculate_forecasting_metrics
from ai.common.serialization import save_artifact
from ai.common.tracking import track_training
from ai.demand_forecasting.config import (
    ARTIFACT_FILENAME,
    DEFAULT_HORIZON_DAYS,
    DEFAULT_LAGS,
    DEFAULT_MODEL_VERSION,
    DEFAULT_ROLLING_WINDOWS,
    XGBOOST_PARAMS,
)
from ai.demand_forecasting.data import chronological_train_test_split, validate_and_load_series
from ai.demand_forecasting.features import generate_feature_matrix


class XGBoostDemandForecaster(BaseForecaster):
    """
    Native XGBoost demand forecaster for Sanjeevani Grid.
    Inherits from BaseForecaster and provides type-safe, leak-free training and inference.
    """

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        model_version: str = DEFAULT_MODEL_VERSION,
        feature_names: Optional[List[str]] = None,
        lags: Optional[List[int]] = None,
        windows: Optional[List[int]] = None,
    ) -> None:
        super().__init__(model_name="XGBoostDemandForecaster")
        self.params = dict(params or XGBOOST_PARAMS)
        if "n_estimators" in self.params:
            self.num_boost_round = int(self.params.pop("n_estimators"))
        else:
            self.num_boost_round = 60
        if "random_state" in self.params:
            self.params["seed"] = self.params.pop("random_state")

        self.model_version = model_version
        self.feature_names = feature_names or []
        self.lags = lags or DEFAULT_LAGS
        self.windows = windows or DEFAULT_ROLLING_WINDOWS
        self.booster: Optional[xgb.Booster] = None
        self.validation_metrics: Dict[str, float] = {}
        self.residual_std: float = 0.0
        self.confidence: float = 0.0

    def fit(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[np.ndarray, pd.Series, List[float]],
        X_val: Optional[Union[np.ndarray, pd.DataFrame]] = None,
        y_val: Optional[Union[np.ndarray, pd.Series, List[float]]] = None,
        num_boost_round: Optional[int] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> "XGBoostDemandForecaster":
        """
        Fit native XGBoost booster on chronological feature matrix and target.
        Computes real validation residuals and empirical confidence score.
        """
        actual_rounds = num_boost_round or self.num_boost_round
        # Feature names extraction
        if isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)
            X_arr = X.values.astype(np.float32)
        else:
            X_arr = np.asarray(X, dtype=np.float32)
            if not self.feature_names:
                self.feature_names = [f"f{i}" for i in range(X_arr.shape[1])]

        y_arr = np.asarray(y, dtype=np.float32).ravel()

        dtrain = xgb.DMatrix(X_arr, label=y_arr, feature_names=self.feature_names)
        evals = [(dtrain, "train")]

        if X_val is not None and y_val is not None:
            if isinstance(X_val, pd.DataFrame):
                X_val_arr = X_val[self.feature_names].values.astype(np.float32)
            else:
                X_val_arr = np.asarray(X_val, dtype=np.float32)
            y_val_arr = np.asarray(y_val, dtype=np.float32).ravel()
            dval = xgb.DMatrix(X_val_arr, label=y_val_arr, feature_names=self.feature_names)
            evals.append((dval, "val"))

        # Train native booster
        self.booster = xgb.train(
            params=self.params,
            dtrain=dtrain,
            num_boost_round=actual_rounds,
            evals=evals if len(evals) > 1 else None,
            verbose_eval=verbose,
        )
        self.is_fitted = True

        # Calculate actual empirical residuals and validation metrics
        if X_val is not None and y_val is not None:
            preds_val = self.booster.predict(dval)
            preds_val = np.maximum(0.0, preds_val)
            self.validation_metrics = calculate_forecasting_metrics(y_val_arr, preds_val)
            residuals = y_val_arr - preds_val
            self.residual_std = float(np.std(residuals))
            mean_actual = float(np.mean(y_val_arr))
            norm_rmse = self.validation_metrics["rmse"] / (mean_actual + 1e-6)
            self.confidence = float(np.clip(1.0 / (1.0 + norm_rmse), 0.05, 0.99))
        else:
            preds_train = self.booster.predict(dtrain)
            preds_train = np.maximum(0.0, preds_train)
            self.validation_metrics = calculate_forecasting_metrics(y_arr, preds_train)
            residuals = y_arr - preds_train
            self.residual_std = float(np.std(residuals))
            mean_actual = float(np.mean(y_arr))
            norm_rmse = self.validation_metrics["rmse"] / (mean_actual + 1e-6)
            self.confidence = float(np.clip(1.0 / (1.0 + norm_rmse), 0.05, 0.99))

        track_training(
            model_name="XGBoostDemandForecaster",
            model_version=self.model_version,
            params=self.params,
            metrics=self.validation_metrics,
            booster=self.booster,
            experiment_name="demand-forecasting",
        )

        return self

    def predict(self, X: Union[np.ndarray, pd.DataFrame], **kwargs: Any) -> np.ndarray:
        """
        Generate non-negative demand forecasts from input feature matrix.
        """
        if not self.is_fitted or self.booster is None:
            raise RuntimeError("XGBoostDemandForecaster must be fitted before predict.")

        if isinstance(X, pd.DataFrame):
            X_arr = X[self.feature_names].values.astype(np.float32)
        else:
            X_arr = np.asarray(X, dtype=np.float32)

        dmatrix = xgb.DMatrix(X_arr, feature_names=self.feature_names)
        raw_preds = self.booster.predict(dmatrix)
        return np.maximum(0.0, raw_preds)


def train_demand_pipeline(
    records: Any,
    test_size: Union[int, float] = 7,
    model_version: str = DEFAULT_MODEL_VERSION,
    params: Optional[Dict[str, Any]] = None,
    save_path: Optional[Union[str, Path]] = None,
) -> Tuple[XGBoostDemandForecaster, Dict[str, float]]:
    """
    End-to-end pipeline: load data, generate features, split chronologically,
    fit XGBoost forecaster, calculate holdout metrics, and optionally persist artifact.
    """
    df_clean = validate_and_load_series(records)
    feat_df, feature_cols = generate_feature_matrix(df_clean, target_col="quantity")

    train_df, test_df = chronological_train_test_split(feat_df, test_size=test_size)

    X_train = train_df[feature_cols]
    y_train = train_df["quantity"].values
    X_test = test_df[feature_cols]
    y_test = test_df["quantity"].values

    forecaster = XGBoostDemandForecaster(
        params=params,
        model_version=model_version,
        feature_names=feature_cols,
    )
    forecaster.fit(X_train, y_train, X_val=X_test, y_val=y_test)

    if save_path:
        forecaster.save(save_path)

    return forecaster, forecaster.validation_metrics


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "demand_forecasting.train", "status": "placeholder"}
