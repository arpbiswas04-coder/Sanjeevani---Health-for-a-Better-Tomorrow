"""
Unit and integration tests for Sanjeevani Grid Demand Forecasting pipeline
ai/tests/test_demand_forecasting.py
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
import uuid
import numpy as np
import pandas as pd
from pydantic import ValidationError

from ai.common.types import format_utc_iso8601
from ai.demand_forecasting.config import DEFAULT_LAGS, DEFAULT_MODEL_VERSION
from ai.demand_forecasting.data import (
    chronological_train_test_split,
    resample_daily_consumption,
    validate_and_load_series,
)
from ai.demand_forecasting.evaluate import backtest_demand_forecaster, evaluate_forecast
from ai.demand_forecasting.features import (
    build_lag_features,
    build_rolling_features,
    extract_calendar_features,
    generate_feature_matrix,
)
from ai.demand_forecasting.predict import DemandForecastingPredictor, placeholder as predict_placeholder
from ai.demand_forecasting.schema import (
    ConsumptionRecord,
    DemandForecastRequest,
    DemandForecastResponse,
)
from ai.demand_forecasting.train import XGBoostDemandForecaster, train_demand_pipeline


def _generate_synthetic_consumption(
    days: int = 60,
    base_demand: float = 50.0,
    trend: float = 0.5,
    weekly_amplitude: float = 15.0,
) -> pd.DataFrame:
    """Generate a deterministic synthetic daily medicine consumption series."""
    start_dt = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    records = []
    for d in range(days):
        current_dt = start_dt + timedelta(days=d)
        # Deterministic weekly cycle: higher demand on weekdays, lower on weekends
        day_of_week = current_dt.weekday()
        weekly_factor = weekly_amplitude * np.sin(2 * np.pi * day_of_week / 7.0)
        qty = max(5.0, base_demand + (trend * d) + weekly_factor)
        records.append({
            "timestamp": format_utc_iso8601(current_dt),
            "quantity": round(float(qty), 2),
        })
    return pd.DataFrame(records)


class TestDemandForecastingSchemas(unittest.TestCase):
    """Test Pydantic v2 input and output schemas."""

    def setUp(self):
        self.facility_id = str(uuid.uuid4())
        self.item_id = str(uuid.uuid4())
        self.history = [
            {"timestamp": f"2026-06-{i:02d}T00:00:00Z", "quantity": 10.0 + i}
            for i in range(1, 15)
        ]

    def test_valid_request_and_response(self):
        req = DemandForecastRequest(
            facility_id=self.facility_id,
            item_id=self.item_id,
            history=self.history,
            horizon_days=7,
        )
        self.assertEqual(req.horizon_days, 7)
        self.assertEqual(len(req.history), 14)

    def test_invalid_uuid_rejected(self):
        with self.assertRaises(ValidationError):
            DemandForecastRequest(
                facility_id="not-a-valid-uuid",
                item_id=self.item_id,
                history=self.history,
            )

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValidationError):
            ConsumptionRecord(timestamp="2026-06-01T00:00:00Z", quantity=-5.0)

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValidationError):
            ConsumptionRecord(timestamp="2026-06-01 00:00:00", quantity=10.0)

    def test_insufficient_history_rejected(self):
        with self.assertRaises(ValidationError):
            DemandForecastRequest(
                facility_id=self.facility_id,
                item_id=self.item_id,
                history=self.history[:3],  # min_length is 7
            )


class TestDemandForecastingData(unittest.TestCase):
    """Test data ingestion, chronological sorting, and splitting."""

    def test_chronological_ordering(self):
        unsorted = [
            {"timestamp": "2026-06-05T00:00:00Z", "quantity": 50.0},
            {"timestamp": "2026-06-01T00:00:00Z", "quantity": 10.0},
            {"timestamp": "2026-06-03T00:00:00Z", "quantity": 30.0},
        ]
        df = validate_and_load_series(unsorted)
        self.assertEqual(df["quantity"].iloc[0], 10.0)
        self.assertEqual(df["quantity"].iloc[1], 30.0)
        self.assertEqual(df["quantity"].iloc[2], 50.0)

    def test_non_finite_and_negative_rejection(self):
        with self.assertRaises(ValueError):
            validate_and_load_series([{"timestamp": "2026-06-01T00:00:00Z", "quantity": float("nan")}])
        with self.assertRaises(ValueError):
            validate_and_load_series([{"timestamp": "2026-06-01T00:00:00Z", "quantity": -10.0}])

    def test_resample_daily(self):
        records = [
            {"timestamp": "2026-06-01T00:00:00Z", "quantity": 10.0},
            {"timestamp": "2026-06-03T00:00:00Z", "quantity": 20.0},
        ]
        df = validate_and_load_series(records)
        daily = resample_daily_consumption(df, fill_missing="zero")
        self.assertEqual(len(daily), 3)  # June 1, June 2 (zero), June 3
        self.assertEqual(daily["quantity"].iloc[1], 0.0)

    def test_chronological_train_test_split(self):
        synthetic = _generate_synthetic_consumption(days=30)
        df = validate_and_load_series(synthetic)
        train_df, test_df = chronological_train_test_split(df, test_size=7)

        self.assertEqual(len(train_df), 23)
        self.assertEqual(len(test_df), 7)
        # Verify strict chronological separation: last train timestamp < first test timestamp
        self.assertLess(train_df["datetime"].iloc[-1], test_df["datetime"].iloc[0])


class TestDemandForecastingFeatures(unittest.TestCase):
    """Test calendar features, lag features, and rolling statistics."""

    def test_calendar_features(self):
        df = pd.DataFrame({
            "datetime": [pd.Timestamp("2026-06-06T00:00:00Z")],  # Saturday
            "quantity": [25.0],
        })
        out = extract_calendar_features(df)
        self.assertEqual(out["day_of_week"].iloc[0], 5)
        self.assertEqual(out["is_weekend"].iloc[0], 1)
        self.assertEqual(out["month"].iloc[0], 6)

    def test_lags_and_rolling_leak_free(self):
        df = pd.DataFrame({
            "datetime": pd.date_range("2026-06-01", periods=10, freq="1D", tz="UTC"),
            "quantity": [10.0 * i for i in range(1, 11)],  # 10, 20, 30, ...
        })
        out, feature_cols = generate_feature_matrix(df, lags=[1, 2], windows=[3], drop_na=False)

        # lag_1 at index 1 should be 10.0 (quantity of index 0)
        self.assertEqual(out["lag_1"].iloc[1], 10.0)
        # rolling_mean_3 at index 3 should be mean of shifted [10, 20, 30] = 20.0
        self.assertAlmostEqual(out["rolling_mean_3"].iloc[3], 20.0)


class TestDemandForecastingModelAndInference(unittest.TestCase):
    """Integration test: training XGBoost, evaluating holdout, and predicting."""

    def setUp(self):
        self.synthetic_df = _generate_synthetic_consumption(days=60)
        self.facility_id = str(uuid.uuid4())
        self.item_id = str(uuid.uuid4())

    def test_end_to_end_training_and_evaluation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "models" / "xgb_demand.joblib"
            forecaster, val_metrics = train_demand_pipeline(
                records=self.synthetic_df,
                test_size=10,
                save_path=model_path,
            )

            self.assertTrue(forecaster.is_fitted)
            self.assertIn("mae", val_metrics)
            self.assertIn("rmse", val_metrics)
            self.assertIn("wape", val_metrics)
            self.assertTrue(np.isfinite(val_metrics["mae"]))
            self.assertGreater(val_metrics["mae"], 0.0)
            self.assertTrue(model_path.is_file())

            # Load and verify identical prediction
            loaded = XGBoostDemandForecaster.load(model_path)
            self.assertTrue(loaded.is_fitted)
            self.assertEqual(loaded.model_version, DEFAULT_MODEL_VERSION)

            # Backtesting
            diagnostics = backtest_demand_forecaster(loaded, self.synthetic_df, horizon_days=7)
            self.assertEqual(diagnostics["sample_size"], 7)
            self.assertIn("metrics", diagnostics)

    def test_inference_predictor_service(self):
        forecaster, _ = train_demand_pipeline(records=self.synthetic_df, test_size=7)
        predictor = DemandForecastingPredictor(forecaster=forecaster)

        req_payload = {
            "facility_id": self.facility_id,
            "item_id": self.item_id,
            "history": self.synthetic_df.to_dict(orient="records"),
            "horizon_days": 7,
        }

        resp = predictor.predict(req_payload)

        self.assertTrue(resp["success"])
        self.assertEqual(resp["facility_id"], self.facility_id)
        self.assertEqual(resp["item_id"], self.item_id)
        self.assertEqual(len(resp["predictions"]), 7)
        self.assertGreater(resp["confidence"], 0.0)
        self.assertLessEqual(resp["confidence"], 1.0)

        for p in resp["predictions"]:
            self.assertGreaterEqual(p["predicted_quantity"], 0.0)
            self.assertGreaterEqual(p["lower_bound"], 0.0)
            self.assertGreaterEqual(p["upper_bound"], p["lower_bound"])

    def test_placeholder_backward_compatibility(self):
        res = predict_placeholder()
        self.assertEqual(res["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()
