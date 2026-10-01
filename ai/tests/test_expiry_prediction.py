"""
Sanjeevani Grid - Expiry Prediction Unit Tests
ai/tests/test_expiry_prediction.py

Covers the full Phase 4 expiry prediction pipeline:
  - ExpiryPredictionRequest schema validation
  - ExpiryPredictionResponse schema validation
  - Feature engineering (build_expiry_features, parse_expiry_to_days)
  - Inference service (ExpiryPredictor.predict)
  - Training pipeline (ExpiryCoverageForecaster, train_expiry_pipeline)
  - Evaluation utilities (evaluate_expiry_predictions)
  - Data ingestion layer (validate_and_load_expiry_records)
"""

import unittest
import uuid

from pydantic import ValidationError

from ai.common.types import RiskLevel, is_valid_utc_iso8601, is_valid_uuid_v4
from ai.expiry_prediction.config import (
    DEFAULT_MODEL_VERSION,
    WASTAGE_CRITICAL_RATIO,
    WASTAGE_HIGH_RATIO,
    WASTAGE_MODERATE_RATIO,
)
from ai.expiry_prediction.data import validate_and_load_expiry_records
from ai.expiry_prediction.evaluate import evaluate_expiry_predictions
from ai.expiry_prediction.features import build_expiry_features
from ai.expiry_prediction.predict import ExpiryPredictor, placeholder
from ai.expiry_prediction.schema import (
    ExpiryPredictionRequest,
    ExpiryPredictionResponse,
    parse_expiry_to_days,
)
from ai.expiry_prediction.train import (
    ExpiryCoverageForecaster,
    train_expiry_pipeline,
)

FACILITY_ID = str(uuid.uuid4())
ITEM_ID = str(uuid.uuid4())
BATCH_ID = "BATCH-2026-9021"


def _make_expiry_request(**overrides) -> dict:
    base = {
        "facility_id": FACILITY_ID,
        "item_id": ITEM_ID,
        "batch_id": BATCH_ID,
        "batch_expiry": "30",
        "batch_stock": 100.0,
        "current_consumption": 5.0,
        "forecast_consumption": 5.0,
        "unit_cost": 12.50,
    }
    base.update(overrides)
    return base


class TestExpiryRequestSchema(unittest.TestCase):
    """Pydantic v2 request schema validation for expiry prediction."""

    def test_valid_request_accepted(self):
        req = ExpiryPredictionRequest.model_validate(_make_expiry_request())
        self.assertEqual(req.batch_stock, 100.0)
        self.assertEqual(req.current_consumption, 5.0)
        self.assertEqual(req.unit_cost, 12.50)

    def test_uuid_v4_validated(self):
        req = ExpiryPredictionRequest.model_validate(_make_expiry_request())
        self.assertTrue(is_valid_uuid_v4(req.facility_id))
        self.assertTrue(is_valid_uuid_v4(req.item_id))

    def test_invalid_uuid_rejected(self):
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(facility_id="not-a-uuid"))
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(item_id="not-a-uuid"))

    def test_negative_values_rejected(self):
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(batch_stock=-1.0))
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(current_consumption=-0.1))
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(forecast_consumption=-2.0))
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(unit_cost=-10.0))

    def test_zero_values_accepted(self):
        req = ExpiryPredictionRequest.model_validate(_make_expiry_request(
            batch_stock=0.0,
            current_consumption=0.0,
            forecast_consumption=0.0,
            unit_cost=0.0,
        ))
        self.assertEqual(req.batch_stock, 0.0)
        self.assertEqual(req.unit_cost, 0.0)

    def test_extra_fields_rejected(self):
        with self.assertRaises(ValidationError):
            ExpiryPredictionRequest.model_validate(_make_expiry_request(unexpected_col=123))

    def test_parse_expiry_to_days_numeric(self):
        self.assertEqual(parse_expiry_to_days(30), 30.0)
        self.assertEqual(parse_expiry_to_days("45.5"), 45.5)

    def test_parse_expiry_to_days_iso_date(self):
        days = parse_expiry_to_days("2099-01-01T00:00:00Z")
        self.assertGreater(days, 0.0)

    def test_parse_expiry_invalid_string(self):
        with self.assertRaises(ValueError):
            parse_expiry_to_days("invalid-date-string-abc")


class TestExpiryResponseSchema(unittest.TestCase):
    """Pydantic v2 response schema validation."""

    def _make_response(self, **overrides) -> dict:
        base = {
            "facility_id": FACILITY_ID,
            "item_id": ITEM_ID,
            "batch_id": BATCH_ID,
            "model_version": DEFAULT_MODEL_VERSION,
            "batch_expiry": "30",
            "days_to_expiry": 30.0,
            "batch_stock": 100.0,
            "projected_consumption": 100.0,
            "likely_unused_quantity": 0.0,
            "wastage_risk": RiskLevel.LOW,
            "wastage_ratio": 0.0,
            "estimated_financial_loss": 0.0,
        }
        base.update(overrides)
        return base

    def test_valid_response_accepted(self):
        resp = ExpiryPredictionResponse.model_validate(self._make_response())
        self.assertTrue(is_valid_uuid_v4(resp.prediction_id))
        self.assertTrue(is_valid_utc_iso8601(resp.generated_at))
        self.assertEqual(resp.wastage_risk, RiskLevel.LOW)

    def test_canonical_risk_levels_supported(self):
        for risk in (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL):
            resp = ExpiryPredictionResponse.model_validate(self._make_response(wastage_risk=risk))
            self.assertEqual(resp.wastage_risk, risk)

    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            ExpiryPredictionResponse.model_validate(self._make_response(extra="bad"))


class TestExpiryFeatures(unittest.TestCase):
    """Unit tests for feature derivation in expiry prediction."""

    def test_full_consumption_zero_unused(self):
        # 30 days * 5/day = 150 units projected, stock = 100 -> 0 unused
        feat = build_expiry_features({
            "batch_stock": 100.0,
            "current_consumption": 5.0,
            "forecast_consumption": 5.0,
            "days_to_expiry": 30.0,
            "unit_cost": 10.0,
        })
        self.assertEqual(feat["likely_unused_quantity"], 0.0)
        self.assertEqual(feat["wastage_ratio"], 0.0)
        self.assertEqual(feat["estimated_financial_loss"], 0.0)

    def test_partial_consumption_positive_unused(self):
        # 10 days * 5/day = 50 units projected, stock = 100 -> 50 unused
        feat = build_expiry_features({
            "batch_stock": 100.0,
            "current_consumption": 5.0,
            "forecast_consumption": 5.0,
            "days_to_expiry": 10.0,
            "unit_cost": 10.0,
        })
        self.assertEqual(feat["likely_unused_quantity"], 50.0)
        self.assertEqual(feat["wastage_ratio"], 0.5)
        self.assertEqual(feat["estimated_financial_loss"], 500.0)

    def test_zero_days_to_expiry(self):
        # Already expired -> all 100 stock unused
        feat = build_expiry_features({
            "batch_stock": 100.0,
            "current_consumption": 5.0,
            "forecast_consumption": 5.0,
            "days_to_expiry": 0.0,
            "unit_cost": 10.0,
        })
        self.assertEqual(feat["likely_unused_quantity"], 100.0)
        self.assertEqual(feat["wastage_ratio"], 1.0)
        self.assertEqual(feat["estimated_financial_loss"], 1000.0)

    def test_zero_consumption_all_unused(self):
        feat = build_expiry_features({
            "batch_stock": 100.0,
            "current_consumption": 0.0,
            "forecast_consumption": 0.0,
            "days_to_expiry": 30.0,
            "unit_cost": 10.0,
        })
        self.assertEqual(feat["likely_unused_quantity"], 100.0)
        self.assertEqual(feat["wastage_ratio"], 1.0)

    def test_fallback_to_current_consumption(self):
        # forecast=0, current=4 -> 4 * 10 = 40 projected, 60 unused
        feat = build_expiry_features({
            "batch_stock": 100.0,
            "current_consumption": 4.0,
            "forecast_consumption": 0.0,
            "days_to_expiry": 10.0,
            "unit_cost": 5.0,
        })
        self.assertEqual(feat["projected_consumption"], 40.0)
        self.assertEqual(feat["likely_unused_quantity"], 60.0)

    def test_missing_numeric_field_raises(self):
        with self.assertRaises(ValueError):
            build_expiry_features({
                "batch_stock": 100.0,
                "current_consumption": 5.0,
                "days_to_expiry": 10.0,
            })


class TestExpiryPredictorInference(unittest.TestCase):
    """Inference tests verifying the four canonical risk levels and outputs."""

    def setUp(self):
        self.predictor = ExpiryPredictor()

    def test_low_risk_fully_consumed(self):
        # 30 days * 5 = 150 projected >= 100 stock -> 0% wastage -> LOW
        res = self.predictor.predict(_make_expiry_request(
            batch_stock=100.0,
            days_to_expiry=30.0,
            forecast_consumption=5.0,
        ))
        self.assertEqual(res["wastage_risk"], RiskLevel.LOW)
        self.assertEqual(res["likely_unused_quantity"], 0.0)
        self.assertEqual(res["estimated_financial_loss"], 0.0)

    def test_moderate_risk_wastage(self):
        # 10 days * 9 = 90 projected, stock = 100 -> 10 unused -> 10% wastage -> MODERATE (>= 5%, < 20%)
        res = self.predictor.predict(_make_expiry_request(
            batch_stock=100.0,
            days_to_expiry=10.0,
            forecast_consumption=9.0,
            unit_cost=10.0,
        ))
        self.assertEqual(res["wastage_risk"], RiskLevel.MODERATE)
        self.assertEqual(res["likely_unused_quantity"], 10.0)
        self.assertEqual(res["estimated_financial_loss"], 100.0)

    def test_high_risk_wastage(self):
        # 10 days * 7 = 70 projected, stock = 100 -> 30 unused -> 30% wastage -> HIGH (>= 20%, < 50%)
        res = self.predictor.predict(_make_expiry_request(
            batch_stock=100.0,
            days_to_expiry=10.0,
            forecast_consumption=7.0,
        ))
        self.assertEqual(res["wastage_risk"], RiskLevel.HIGH)
        self.assertEqual(res["likely_unused_quantity"], 30.0)

    def test_critical_risk_wastage(self):
        # 10 days * 2 = 20 projected, stock = 100 -> 80 unused -> 80% wastage -> CRITICAL (>= 50%)
        res = self.predictor.predict(_make_expiry_request(
            batch_stock=100.0,
            days_to_expiry=10.0,
            forecast_consumption=2.0,
        ))
        self.assertEqual(res["wastage_risk"], RiskLevel.CRITICAL)
        self.assertEqual(res["likely_unused_quantity"], 80.0)

    def test_already_expired_critical_risk(self):
        res = self.predictor.predict(_make_expiry_request(
            batch_stock=100.0,
            days_to_expiry=0.0,
            forecast_consumption=10.0,
        ))
        self.assertEqual(res["wastage_risk"], RiskLevel.CRITICAL)
        self.assertEqual(res["likely_unused_quantity"], 100.0)

    def test_zero_stock_low_risk(self):
        res = self.predictor.predict(_make_expiry_request(
            batch_stock=0.0,
            days_to_expiry=10.0,
            forecast_consumption=5.0,
        ))
        self.assertEqual(res["wastage_risk"], RiskLevel.LOW)
        self.assertEqual(res["likely_unused_quantity"], 0.0)

    def test_deterministic_repeated_inference(self):
        req = _make_expiry_request()
        r1 = self.predictor.predict(req)
        r2 = self.predictor.predict(req)
        for key in ("likely_unused_quantity", "wastage_risk", "wastage_ratio", "estimated_financial_loss"):
            self.assertEqual(r1[key], r2[key])

    def test_placeholder_backward_compatibility(self):
        res = placeholder()
        self.assertEqual(res["status"], "placeholder")
        self.assertEqual(res["module"], "expiry_prediction.predict")


class TestExpiryTrainingAndEvaluation(unittest.TestCase):
    """Test training pipeline lifecycle and evaluation metrics."""

    def test_forecaster_lifecycle(self):
        records = [_make_expiry_request(), _make_expiry_request(batch_stock=50.0)]
        forecaster = ExpiryCoverageForecaster()
        self.assertFalse(forecaster.is_fitted)
        forecaster.fit(records)
        self.assertTrue(forecaster.is_fitted)

        preds = forecaster.predict(records)
        self.assertEqual(len(preds), 2)
        self.assertIn("likely_unused_quantity", preds[0])

    def test_predict_before_fit_raises(self):
        forecaster = ExpiryCoverageForecaster()
        with self.assertRaises(RuntimeError):
            forecaster.predict([_make_expiry_request()])

    def test_train_expiry_pipeline(self):
        records = [_make_expiry_request()]
        model, meta = train_expiry_pipeline(records)
        self.assertTrue(model.is_fitted)
        self.assertEqual(meta["sample_size"], 1)

    def test_evaluate_expiry_predictions(self):
        records = [
            _make_expiry_request(batch_stock=100.0, days_to_expiry=1.0, forecast_consumption=1.0),  # wastage positive
            _make_expiry_request(batch_stock=10.0, days_to_expiry=30.0, forecast_consumption=5.0), # wastage 0
        ]
        y_true = [1, 0]
        metrics = evaluate_expiry_predictions(records, y_true)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["f1"], 1.0)


class TestExpiryDataLayer(unittest.TestCase):
    """Test data loading and validation."""

    def test_valid_records_to_dataframe(self):
        df = validate_and_load_expiry_records([_make_expiry_request()])
        self.assertEqual(len(df), 1)
        self.assertIn("batch_stock", df.columns)

    def test_empty_records_raise(self):
        with self.assertRaises(ValueError):
            validate_and_load_expiry_records([])


if __name__ == "__main__":
    unittest.main()
