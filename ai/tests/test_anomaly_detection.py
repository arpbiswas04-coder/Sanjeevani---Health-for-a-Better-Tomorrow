"""
Sanjeevani Grid - Anomaly Detection Unit Tests
ai/tests/test_anomaly_detection.py

Covers the full Phase 4 anomaly detection pipeline:
  - AnomalyDetectionRequest schema validation
  - AnomalyDetectionResponse schema validation
  - Statistical feature engineering (compute_robust_zscore)
  - Inference service (AnomalyDetectorPredictor.predict) across all documented target domains:
      * sudden_inventory_decrease
      * abnormal_consumption
      * unusual_disease_count
      * unexpected_attendance_drop
      * suspicious_manual_stock_adjustment
  - Zero-variance / constant baseline edge cases
  - Canonical RiskLevel classification
  - Training pipeline (RobustZScoreAnomalyDetector, train_anomaly_pipeline)
  - Evaluation utilities (evaluate_anomaly_predictions)
"""

import unittest
import uuid

from pydantic import ValidationError

from ai.anomaly_detection.config import (
    DEFAULT_MODEL_VERSION,
    TARGET_ABNORMAL_CONSUMPTION,
    TARGET_SUDDEN_INVENTORY_DECREASE,
    TARGET_SUSPICIOUS_MANUAL_STOCK_ADJUSTMENT,
    TARGET_UNEXPECTED_ATTENDANCE_DROP,
    TARGET_UNUSUAL_DISEASE_COUNT,
    VALID_ANOMALY_TARGETS,
)
from ai.anomaly_detection.data import validate_and_load_anomaly_records
from ai.anomaly_detection.evaluate import (
    evaluate_anomaly_predictions,
    evaluate_records_anomaly,
)
from ai.anomaly_detection.features import compute_robust_zscore
from ai.anomaly_detection.predict import AnomalyDetectorPredictor, placeholder
from ai.anomaly_detection.schema import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
)
from ai.anomaly_detection.train import (
    RobustZScoreAnomalyDetector,
    train_anomaly_pipeline,
)
from ai.common.types import RiskLevel, is_valid_utc_iso8601, is_valid_uuid_v4

FACILITY_ID = str(uuid.uuid4())
ITEM_ID = str(uuid.uuid4())


def _make_anomaly_request(**overrides) -> dict:
    base = {
        "facility_id": FACILITY_ID,
        "item_id": ITEM_ID,
        "target_type": TARGET_ABNORMAL_CONSUMPTION,
        "current_value": 50.0,
        "history": [48.0, 50.0, 52.0, 49.0, 51.0, 50.0, 48.0],
        "z_threshold": 3.0,
    }
    base.update(overrides)
    return base


class TestAnomalyRequestSchema(unittest.TestCase):
    """Pydantic v2 request schema validation."""

    def test_valid_request_accepted(self):
        req = AnomalyDetectionRequest.model_validate(_make_anomaly_request())
        self.assertEqual(req.current_value, 50.0)
        self.assertEqual(len(req.history), 7)

    def test_uuid_v4_validated(self):
        req = AnomalyDetectionRequest.model_validate(_make_anomaly_request())
        self.assertTrue(is_valid_uuid_v4(req.facility_id))
        self.assertTrue(is_valid_uuid_v4(req.item_id))

    def test_invalid_uuid_rejected(self):
        with self.assertRaises(ValidationError):
            AnomalyDetectionRequest.model_validate(_make_anomaly_request(facility_id="bad-uuid"))
        with self.assertRaises(ValidationError):
            AnomalyDetectionRequest.model_validate(_make_anomaly_request(item_id="bad-uuid"))

    def test_insufficient_history_rejected(self):
        with self.assertRaises(ValidationError):
            AnomalyDetectionRequest.model_validate(_make_anomaly_request(history=[10.0, 20.0]))

    def test_empty_target_type_rejected(self):
        with self.assertRaises(ValidationError):
            AnomalyDetectionRequest.model_validate(_make_anomaly_request(target_type="   "))

    def test_extra_fields_rejected(self):
        with self.assertRaises(ValidationError):
            AnomalyDetectionRequest.model_validate(_make_anomaly_request(extra_field="unknown"))


class TestAnomalyResponseSchema(unittest.TestCase):
    """Pydantic v2 response schema validation."""

    def _make_response(self, **overrides) -> dict:
        base = {
            "facility_id": FACILITY_ID,
            "item_id": ITEM_ID,
            "target_type": TARGET_ABNORMAL_CONSUMPTION,
            "model_version": DEFAULT_MODEL_VERSION,
            "current_value": 50.0,
            "baseline_median": 50.0,
            "baseline_mad": 1.0,
            "z_score": 0.0,
            "is_anomaly": False,
            "risk_level": RiskLevel.LOW,
            "direction": "normal",
            "details": {},
        }
        base.update(overrides)
        return base

    def test_valid_response_accepted(self):
        resp = AnomalyDetectionResponse.model_validate(self._make_response())
        self.assertTrue(is_valid_uuid_v4(resp.prediction_id))
        self.assertTrue(is_valid_utc_iso8601(resp.generated_at))
        self.assertEqual(resp.risk_level, RiskLevel.LOW)

    def test_canonical_risk_levels_supported(self):
        for risk in (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL):
            resp = AnomalyDetectionResponse.model_validate(self._make_response(risk_level=risk))
            self.assertEqual(resp.risk_level, risk)


class TestRobustZScoreFeatures(unittest.TestCase):
    """Tests for robust z-score calculation and directionality."""

    def test_normal_value_near_zero_zscore(self):
        history = [10.0, 12.0, 11.0, 9.0, 10.0, 11.0, 10.0]
        res = compute_robust_zscore(10.0, history)
        self.assertAlmostEqual(res["z_score"], 0.0, places=2)
        self.assertFalse(res["is_anomaly"])
        self.assertEqual(res["direction"], "normal")

    def test_positive_surge_anomaly(self):
        history = [10.0, 11.0, 9.0, 10.0, 12.0, 10.0]
        # Massive surge
        res = compute_robust_zscore(50.0, history, z_threshold=3.0)
        self.assertTrue(res["is_anomaly"])
        self.assertGreater(res["z_score"], 3.0)
        self.assertEqual(res["direction"], "surge")

    def test_negative_drop_anomaly(self):
        history = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0]
        # Sudden drop
        res = compute_robust_zscore(10.0, history, z_threshold=3.0)
        self.assertTrue(res["is_anomaly"])
        self.assertLess(res["z_score"], -3.0)
        self.assertEqual(res["direction"], "drop")

    def test_zero_variance_history_constant(self):
        history = [25.0, 25.0, 25.0, 25.0]
        # Exactly equal to constant baseline
        res_exact = compute_robust_zscore(25.0, history)
        self.assertEqual(res_exact["z_score"], 0.0)
        self.assertFalse(res_exact["is_anomaly"])

        # Different from constant baseline
        res_diff = compute_robust_zscore(35.0, history)
        self.assertTrue(res_diff["is_anomaly"])
        self.assertGreater(res_diff["z_score"], 3.0)

    def test_insufficient_history_raises(self):
        with self.assertRaises(ValueError):
            compute_robust_zscore(10.0, [10.0, 12.0])


class TestAnomalyInferenceService(unittest.TestCase):
    """Inference tests covering all documented anomaly targets and risk levels."""

    def setUp(self):
        self.predictor = AnomalyDetectorPredictor()

    def test_documented_targets_accepted(self):
        for target in VALID_ANOMALY_TARGETS:
            req = _make_anomaly_request(target_type=target)
            res = self.predictor.predict(req)
            self.assertEqual(res["target_type"], target)
            self.assertTrue(res["success"])

    def test_risk_level_low_for_normal_value(self):
        history = [100.0, 105.0, 95.0, 100.0, 98.0, 102.0]
        res = self.predictor.predict(_make_anomaly_request(
            current_value=101.0,
            history=history,
        ))
        self.assertEqual(res["risk_level"], RiskLevel.LOW)
        self.assertFalse(res["is_anomaly"])

    def test_risk_level_moderate(self):
        # Median=100, MAD=2 -> scaled_mad≈2.965. Deviation of 6 -> Z ≈ 2.02 -> MODERATE
        history = [100.0, 102.0, 98.0, 100.0, 102.0, 98.0]
        res = self.predictor.predict(_make_anomaly_request(
            current_value=106.5,
            history=history,
        ))
        self.assertEqual(res["risk_level"], RiskLevel.MODERATE)
        self.assertFalse(res["is_anomaly"])

    def test_risk_level_high(self):
        # Deviation giving 3.0 <= Z < 4.5 -> HIGH
        history = [100.0, 102.0, 98.0, 100.0, 102.0, 98.0]
        res = self.predictor.predict(_make_anomaly_request(
            current_value=110.0,
            history=history,
        ))
        self.assertEqual(res["risk_level"], RiskLevel.HIGH)
        self.assertTrue(res["is_anomaly"])

    def test_risk_level_critical(self):
        # Massive anomaly -> Z >= 4.5 -> CRITICAL
        history = [100.0, 102.0, 98.0, 100.0, 102.0, 98.0]
        res = self.predictor.predict(_make_anomaly_request(
            current_value=150.0,
            history=history,
        ))
        self.assertEqual(res["risk_level"], RiskLevel.CRITICAL)
        self.assertTrue(res["is_anomaly"])

    def test_sudden_inventory_decrease_target(self):
        # Rapid drop in inventory
        history = [500.0, 490.0, 510.0, 495.0, 505.0]
        res = self.predictor.predict(_make_anomaly_request(
            target_type=TARGET_SUDDEN_INVENTORY_DECREASE,
            current_value=150.0,
            history=history,
        ))
        self.assertEqual(res["direction"], "drop")
        self.assertTrue(res["is_anomaly"])

    def test_unusual_disease_count_target(self):
        # Disease case surge
        history = [5.0, 6.0, 4.0, 5.0, 7.0, 5.0, 6.0]
        res = self.predictor.predict(_make_anomaly_request(
            target_type=TARGET_UNUSUAL_DISEASE_COUNT,
            current_value=65.0,
            history=history,
        ))
        self.assertEqual(res["direction"], "surge")
        self.assertTrue(res["is_anomaly"])

    def test_deterministic_repeated_prediction(self):
        req = _make_anomaly_request()
        r1 = self.predictor.predict(req)
        r2 = self.predictor.predict(req)
        for key in ("z_score", "is_anomaly", "risk_level", "direction", "baseline_median"):
            self.assertEqual(r1[key], r2[key])

    def test_placeholder_backward_compatibility(self):
        res = placeholder()
        self.assertEqual(res["status"], "placeholder")
        self.assertEqual(res["module"], "anomaly_detection.predict")


class TestAnomalyDetectorTrainingAndEvaluation(unittest.TestCase):
    """Training lifecycle and classification metric evaluation."""

    def test_detector_fit_and_predict(self):
        history = [10.0, 11.0, 9.0, 10.0, 12.0, 10.0]
        detector = RobustZScoreAnomalyDetector()
        self.assertFalse(detector.is_fitted)
        detector.fit(history)
        self.assertTrue(detector.is_fitted)

        preds = detector.predict([10.0, 50.0])
        self.assertEqual(len(preds), 2)
        self.assertFalse(preds[0]["is_anomaly"])
        self.assertTrue(preds[1]["is_anomaly"])

    def test_predict_before_fit_raises(self):
        detector = RobustZScoreAnomalyDetector()
        with self.assertRaises(RuntimeError):
            detector.predict([10.0])

    def test_train_anomaly_pipeline(self):
        history = [10.0, 12.0, 11.0, 10.0]
        model, meta = train_anomaly_pipeline(history)
        self.assertTrue(model.is_fitted)
        self.assertEqual(meta["sample_size"], 4)

    def test_evaluate_anomaly_predictions(self):
        y_true = [0, 1, 0, 1]
        y_pred = [0, 1, 0, 1]
        metrics = evaluate_anomaly_predictions(y_true, y_pred)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["f1"], 1.0)

    def test_evaluate_records_anomaly(self):
        records = [
            {"current_value": 10.0, "history": [10.0, 11.0, 9.0, 10.0]},
            {"current_value": 100.0, "history": [10.0, 11.0, 9.0, 10.0]},
        ]
        metrics = evaluate_records_anomaly(records, [0, 1])
        self.assertEqual(metrics["accuracy"], 1.0)


class TestAnomalyDataLayer(unittest.TestCase):
    """Test data loading and validation."""

    def test_valid_records_to_dataframe(self):
        df = validate_and_load_anomaly_records([_make_anomaly_request()])
        self.assertEqual(len(df), 1)
        self.assertIn("current_value", df.columns)

    def test_empty_records_raise(self):
        with self.assertRaises(ValueError):
            validate_and_load_anomaly_records([])


if __name__ == "__main__":
    unittest.main()
