"""
Unit tests for Sanjeevani Grid shared AI foundation
ai/tests/test_common.py
"""

from datetime import datetime, timezone
import math
from pathlib import Path
import tempfile
import unittest
import uuid

import numpy as np

from ai.common import (
    BaseForecaster,
    BasePredictor,
    BaseScorer,
    RiskLevel,
    calculate_brier_score,
    calculate_classification_metrics,
    calculate_forecasting_metrics,
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    calculate_wape,
    ensure_utc_iso8601,
    ensure_uuid_v4,
    format_utc_iso8601,
    is_valid_utc_iso8601,
    is_valid_uuid_v4,
    load_artifact,
    now_utc_iso8601,
    save_artifact,
)


class DummyForecaster(BaseForecaster):
    """Concrete implementation for testing BaseForecaster."""

    def __init__(self, multiplier: float = 1.0) -> None:
        super().__init__(model_name="DummyForecaster")
        self.multiplier = multiplier

    def fit(self, X, y=None, **kwargs):
        self.is_fitted = True
        return self

    def predict(self, X, **kwargs):
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        arr = np.asarray(X, dtype=np.float64)
        return arr * self.multiplier


class DummyPredictor(BasePredictor):
    """Concrete implementation for testing BasePredictor."""

    def predict(self, payload):
        if "value" not in payload:
            raise ValueError("Missing 'value' in payload")
        return {"result": payload["value"] * 2}


class DummyScorer(BaseScorer):
    """Concrete implementation for testing BaseScorer."""

    def calculate_score(self, features):
        score = float(features.get("index", 0.5))
        if score > 0.8:
            risk = RiskLevel.CRITICAL
        elif score > 0.5:
            risk = RiskLevel.HIGH
        elif score > 0.2:
            risk = RiskLevel.MODERATE
        else:
            risk = RiskLevel.LOW
        return {"resilience_score": score, "risk_level": risk.value}


class TestSharedTypesAndValidators(unittest.TestCase):
    """Tests for RiskLevel and identifier/timestamp validation."""

    def test_canonical_risk_levels(self):
        self.assertEqual(RiskLevel.LOW.value, "low")
        self.assertEqual(RiskLevel.MODERATE.value, "moderate")
        self.assertEqual(RiskLevel.HIGH.value, "high")
        self.assertEqual(RiskLevel.CRITICAL.value, "critical")
        # Ensure it's a string enum
        self.assertIsInstance(RiskLevel.LOW, str)
        self.assertEqual(f"level_{RiskLevel.HIGH}", "level_high")

    def test_uuid_v4_validation(self):
        valid_uuid = str(uuid.uuid4())
        self.assertTrue(is_valid_uuid_v4(valid_uuid))
        self.assertTrue(is_valid_uuid_v4(uuid.UUID(valid_uuid)))

        # UUID v1 should fail UUID v4 check
        uuid_v1 = str(uuid.uuid1())
        self.assertFalse(is_valid_uuid_v4(uuid_v1))

        # Invalid formats
        self.assertFalse(is_valid_uuid_v4("not-a-uuid"))
        self.assertFalse(is_valid_uuid_v4(""))
        self.assertFalse(is_valid_uuid_v4(12345))
        self.assertFalse(is_valid_uuid_v4(None))

    def test_ensure_uuid_v4(self):
        raw_uuid = str(uuid.uuid4()).upper()
        normalized = ensure_uuid_v4(raw_uuid)
        self.assertEqual(normalized, raw_uuid.lower())

        with self.assertRaises(ValueError):
            ensure_uuid_v4("invalid-uuid-string")

    def test_utc_iso8601_validation(self):
        self.assertTrue(is_valid_utc_iso8601("2026-09-30T12:00:00Z"))
        self.assertTrue(is_valid_utc_iso8601("2026-09-30T12:00:00.123456Z"))
        self.assertTrue(is_valid_utc_iso8601("2026-09-30T12:00:00+00:00"))

        # Non-UTC timezone offsets should fail
        self.assertFalse(is_valid_utc_iso8601("2026-09-30T12:00:00+05:30"))
        self.assertFalse(is_valid_utc_iso8601("2026-09-30T12:00:00-04:00"))

        # Naive / non-ISO formats
        self.assertFalse(is_valid_utc_iso8601("2026-09-30 12:00:00"))
        self.assertFalse(is_valid_utc_iso8601("not-a-date"))
        self.assertFalse(is_valid_utc_iso8601(""))
        self.assertFalse(is_valid_utc_iso8601(None))

    def test_ensure_utc_iso8601(self):
        now_dt = datetime.now(timezone.utc)
        formatted = ensure_utc_iso8601(now_dt)
        self.assertTrue(formatted.endswith("Z"))
        self.assertTrue(is_valid_utc_iso8601(formatted))

        # Naive datetime must raise ValueError
        with self.assertRaises(ValueError):
            ensure_utc_iso8601(datetime(2026, 9, 30, 12, 0, 0))

        # Invalid string must raise ValueError
        with self.assertRaises(ValueError):
            ensure_utc_iso8601("invalid-timestamp")

    def test_now_utc_iso8601(self):
        ts = now_utc_iso8601()
        self.assertTrue(ts.endswith("Z"))
        self.assertTrue(is_valid_utc_iso8601(ts))


class TestEvaluationMetrics(unittest.TestCase):
    """Tests for regression and classification evaluation metrics."""

    def test_mae_and_rmse(self):
        y_true = [10.0, 20.0, 30.0]
        y_pred = [12.0, 18.0, 35.0]  # Errors: 2, 2, 5

        mae = calculate_mae(y_true, y_pred)
        self.assertAlmostEqual(mae, 3.0, places=5)

        # RMSE: sqrt((4 + 4 + 25) / 3) = sqrt(11) = 3.31662479
        rmse = calculate_rmse(y_true, y_pred)
        self.assertAlmostEqual(rmse, math.sqrt(33.0 / 3.0), places=5)

    def test_mape_and_wape(self):
        y_true = [100.0, 200.0]
        y_pred = [110.0, 180.0]  # Abs errs: 10, 20

        # MAPE: mean(10/100, 20/200) = mean(0.1, 0.1) = 10.0%
        mape = calculate_mape(y_true, y_pred)
        self.assertAlmostEqual(mape, 10.0, places=5)

        # WAPE: (10 + 20) / (100 + 200) = 30 / 300 = 10.0%
        wape = calculate_wape(y_true, y_pred)
        self.assertAlmostEqual(wape, 10.0, places=5)

    def test_mape_with_zeros(self):
        y_true = [0.0, 100.0]
        y_pred = [5.0, 100.0]
        # Should not throw ZeroDivisionError due to safe epsilon
        mape = calculate_mape(y_true, y_pred)
        self.assertTrue(np.isfinite(mape))

    def test_wape_all_zeros(self):
        self.assertEqual(calculate_wape([0.0, 0.0], [0.0, 0.0]), 0.0)
        self.assertEqual(calculate_wape([0.0, 0.0], [5.0, 5.0]), 100.0)

    def test_forecasting_metrics_dict(self):
        res = calculate_forecasting_metrics([1.0, 2.0], [1.1, 1.9])
        self.assertIn("mae", res)
        self.assertIn("rmse", res)
        self.assertIn("mape", res)
        self.assertIn("wape", res)

    def test_metric_validation_failures(self):
        with self.assertRaises(ValueError):
            calculate_mae([], [])
        with self.assertRaises(ValueError):
            calculate_mae([1.0, 2.0], [1.0])
        with self.assertRaises(ValueError):
            calculate_mae([1.0, float("nan")], [1.0, 2.0])
        with self.assertRaises(ValueError):
            calculate_mae([1.0, 2.0], [1.0, float("inf")])

    def test_brier_score(self):
        y_true = [1, 0, 1, 1]
        y_prob = [0.9, 0.1, 0.8, 0.4]  # errs: 0.1, 0.1, 0.2, 0.6 -> sq: 0.01, 0.01, 0.04, 0.36 -> sum: 0.42 / 4 = 0.105
        brier = calculate_brier_score(y_true, y_prob)
        self.assertAlmostEqual(brier, 0.105, places=5)

        with self.assertRaises(ValueError):
            calculate_brier_score([1, 0], [1.5, 0.2])  # prob out of range
        with self.assertRaises(ValueError):
            calculate_brier_score([2, 0], [0.5, 0.2])  # non-binary true

    def test_classification_metrics(self):
        y_true = [1, 0, 1, 1, 0, 0]
        y_pred = [1, 0, 1, 0, 0, 1]

        metrics = calculate_classification_metrics(y_true, y_pred)
        self.assertIn("accuracy", metrics)
        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertIn("f1", metrics)
        self.assertEqual(metrics["true_positives"], 2)
        self.assertEqual(metrics["false_positives"], 1)
        self.assertEqual(metrics["true_negatives"], 2)
        self.assertEqual(metrics["false_negatives"], 1)


class TestBaseAbstractionsAndSerialization(unittest.TestCase):
    """Tests for BaseForecaster, BasePredictor, BaseScorer and serialization."""

    def test_cannot_instantiate_abstract_base_classes(self):
        with self.assertRaises(TypeError):
            BaseForecaster()
        with self.assertRaises(TypeError):
            BasePredictor()
        with self.assertRaises(TypeError):
            BaseScorer()

    def test_concrete_dummy_forecaster_lifecycle(self):
        model = DummyForecaster(multiplier=2.5)
        self.assertFalse(model.is_fitted)

        with self.assertRaises(RuntimeError):
            model.predict([1.0, 2.0])

        model.fit([1.0, 2.0])
        self.assertTrue(model.is_fitted)
        preds = model.predict([2.0, 4.0])
        np.testing.assert_allclose(preds, [5.0, 10.0])

    def test_serialization_and_deserialization(self):
        model = DummyForecaster(multiplier=3.0)
        model.fit([1.0])

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "models" / "subfolder" / "dummy_model.joblib"
            saved_path = model.save(model_path)
            self.assertTrue(saved_path.is_file())

            loaded_model = DummyForecaster.load(saved_path)
            self.assertIsInstance(loaded_model, DummyForecaster)
            self.assertTrue(loaded_model.is_fitted)
            self.assertEqual(loaded_model.multiplier, 3.0)

            # Test predict on loaded model
            np.testing.assert_allclose(loaded_model.predict([10.0]), [30.0])

    def test_load_nonexistent_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            load_artifact("/non/existent/path/model.joblib")

    def test_concrete_dummy_predictor_and_scorer(self):
        predictor = DummyPredictor()
        res = predictor.predict({"value": 15})
        self.assertEqual(res["result"], 30)

        scorer = DummyScorer()
        score_res = scorer.calculate_score({"index": 0.85})
        self.assertEqual(score_res["risk_level"], "critical")


if __name__ == "__main__":
    unittest.main()
