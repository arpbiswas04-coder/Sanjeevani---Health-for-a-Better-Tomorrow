"""
Sanjeevani Grid - Demand Forecasting Configuration
ai/demand_forecasting/config.py

Hyperparameters, feature engineering windows, and artifact paths.
"""

from typing import Any, Dict, List

DEFAULT_LAGS: List[int] = [1, 2, 3, 7, 14]
DEFAULT_ROLLING_WINDOWS: List[int] = [7, 14]
DEFAULT_HORIZON_DAYS: int = 7
MIN_HISTORY_DAYS: int = 14
DEFAULT_MODEL_VERSION: str = "xgb_demand_v1.0.0"
ARTIFACT_FILENAME: str = "xgboost_demand_forecaster.joblib"

DEFAULT_NUM_BOOST_ROUND: int = 80

# Default XGBoost native booster parameters
XGBOOST_PARAMS: Dict[str, Any] = {
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "seed": 42,
    "objective": "reg:squarederror",
    "nthread": 1,
}


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "demand_forecasting.config", "status": "placeholder"}
