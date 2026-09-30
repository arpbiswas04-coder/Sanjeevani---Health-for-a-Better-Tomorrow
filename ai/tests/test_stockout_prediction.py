"""
Sanjeevani Grid - Stockout Prediction Unit Tests
ai/tests/test_stockout_prediction.py

Covers the full Phase 3 stockout prediction pipeline:
  - StockoutPredictionRequest schema validation
  - StockoutPredictionResponse schema validation
  - Feature engineering (build_stockout_features)
  - Inference service (StockoutPredictor.predict)
  - Training pipeline (StockoutCoverageForecaster, train_stockout_pipeline)
  - Evaluation utilities (evaluate_stockout_predictions)

Test taxonomy aligned with ai/AGENTS.md (Section 8):
  Pydantic schema validation, feature correctness, deterministic output,
  inference contracts, and error handling.
"""

import math
import unittest
import uuid

from pydantic import ValidationError

from ai.common.types import RiskLevel, is_valid_uuid_v4, is_valid_utc_iso8601
from ai.stockout_prediction.config import (
    COVERAGE_CRITICAL_THRESHOLD,
    COVERAGE_MODERATE_THRESHOLD,
    DEFAULT_MODEL_VERSION,
    NEAR_ZERO_CONSUMPTION,
)
from ai.stockout_prediction.data import validate_and_load_records
from ai.stockout_prediction.evaluate import evaluate_stockout_predictions
from ai.stockout_prediction.features import build_stockout_features
from ai.stockout_prediction.predict import StockoutPredictor, placeholder
from ai.stockout_prediction.schema import (
    StockoutPredictionRequest,
    StockoutPredictionResponse,
)
from ai.stockout_prediction.train import (
    StockoutCoverageForecaster,
    train_stockout_pipeline,
)


# ── Shared test fixtures ────────────────────────────────────────────────────

FACILITY_ID = str(uuid.uuid4())
ITEM_ID = str(uuid.uuid4())


def _make_request(**overrides) -> dict:
    """Return a minimal valid stockout request dict, optionally overridden."""
    base = {
        "facility_id": FACILITY_ID,
        "item_id": ITEM_ID,
        "current_quantity": 100.0,
        "predicted_demand": 50.0,
        "daily_consumption": 10.0,
        "supplier_lead_time": 7,
        "pending_purchase_orders": 0.0,
        "incoming_transfers": 0.0,
    }
    base.update(overrides)
    return base


# ── Schema Tests ────────────────────────────────────────────────────────────


class TestStockoutRequestSchema(unittest.TestCase):
    """Pydantic v2 request schema validation."""

    def test_valid_request_accepted(self):
        req = StockoutPredictionRequest.model_validate(_make_request())
        self.assertEqual(req.current_quantity, 100.0)
        self.assertEqual(req.supplier_lead_time, 7)

    def test_uuid_v4_validated_on_facility_and_item(self):
        req = StockoutPredictionRequest.model_validate(_make_request())
        self.assertTrue(is_valid_uuid_v4(req.facility_id))
        self.assertTrue(is_valid_uuid_v4(req.item_id))

    def test_invalid_facility_uuid_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(facility_id="not-a-uuid")
            )

    def test_invalid_item_uuid_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(item_id="bad-id")
            )

    def test_negative_current_quantity_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(current_quantity=-1.0)
            )

    def test_negative_daily_consumption_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(daily_consumption=-0.5)
            )

    def test_negative_predicted_demand_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(predicted_demand=-10.0)
            )

    def test_negative_pending_purchase_orders_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(pending_purchase_orders=-5.0)
            )

    def test_negative_incoming_transfers_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(incoming_transfers=-1.0)
            )

    def test_lead_time_exceeding_365_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(supplier_lead_time=366)
            )

    def test_zero_values_accepted(self):
        """Zero consumption, zero demand, zero orders, zero transfers must all be valid."""
        req = StockoutPredictionRequest.model_validate(
            _make_request(
                current_quantity=0.0,
                predicted_demand=0.0,
                daily_consumption=0.0,
                supplier_lead_time=0,
                pending_purchase_orders=0.0,
                incoming_transfers=0.0,
            )
        )
        self.assertEqual(req.current_quantity, 0.0)

    def test_extra_fields_rejected(self):
        """extra='forbid' should reject unknown keys."""
        with self.assertRaises(ValidationError):
            StockoutPredictionRequest.model_validate(
                _make_request(unexpected_field="oops")
            )

    def test_defaults_for_optional_fields(self):
        """pending_purchase_orders and incoming_transfers should default to 0."""
        data = _make_request()
        data.pop("pending_purchase_orders")
        data.pop("incoming_transfers")
        req = StockoutPredictionRequest.model_validate(data)
        self.assertEqual(req.pending_purchase_orders, 0.0)
        self.assertEqual(req.incoming_transfers, 0.0)


class TestStockoutResponseSchema(unittest.TestCase):
    """Pydantic v2 response schema validation."""

    def _make_response(self, **overrides) -> dict:
        base = {
            "facility_id": FACILITY_ID,
            "item_id": ITEM_ID,
            "model_version": DEFAULT_MODEL_VERSION,
            "stockout_predicted": False,
            "risk_level": RiskLevel.LOW,
            "available_quantity": 100.0,
            "demand_during_lead_time": 70.0,
            "coverage_ratio": 1.43,
        }
        base.update(overrides)
        return base

    def test_valid_response_accepted(self):
        resp = StockoutPredictionResponse.model_validate(self._make_response())
        self.assertTrue(is_valid_uuid_v4(resp.prediction_id))
        self.assertTrue(is_valid_utc_iso8601(resp.generated_at))
        self.assertEqual(resp.success, True)

    def test_risk_level_is_canonical(self):
        resp = StockoutPredictionResponse.model_validate(
            self._make_response(risk_level=RiskLevel.CRITICAL)
        )
        self.assertIsInstance(resp.risk_level, RiskLevel)
        self.assertEqual(resp.risk_level, RiskLevel.CRITICAL)

    def test_days_until_stockout_none_accepted(self):
        resp = StockoutPredictionResponse.model_validate(
            self._make_response(days_until_stockout=None)
        )
        self.assertIsNone(resp.days_until_stockout)

    def test_days_until_stockout_positive_accepted(self):
        resp = StockoutPredictionResponse.model_validate(
            self._make_response(days_until_stockout=5.0)
        )
        self.assertAlmostEqual(resp.days_until_stockout, 5.0)

    def test_negative_available_quantity_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionResponse.model_validate(
                self._make_response(available_quantity=-1.0)
            )

    def test_generated_at_is_utc_iso8601(self):
        resp = StockoutPredictionResponse.model_validate(self._make_response())
        self.assertTrue(is_valid_utc_iso8601(resp.generated_at))

    def test_extra_fields_rejected(self):
        with self.assertRaises(ValidationError):
            StockoutPredictionResponse.model_validate(
                self._make_response(unknown_key="x")
            )


# ── Feature Engineering Tests ───────────────────────────────────────────────


class TestBuildStockoutFeatures(unittest.TestCase):
    """Unit tests for deterministic feature computation."""

    def _raw(self, **overrides) -> dict:
        base = {
            "current_quantity": 100.0,
            "predicted_demand": 50.0,
            "daily_consumption": 10.0,
            "supplier_lead_time": 7,
            "pending_purchase_orders": 0.0,
            "incoming_transfers": 0.0,
        }
        base.update(overrides)
        return base

    def test_available_quantity_aggregation(self):
        feat = build_stockout_features(
            self._raw(
                current_quantity=80.0,
                pending_purchase_orders=15.0,
                incoming_transfers=5.0,
            )
        )
        self.assertAlmostEqual(feat["available_quantity"], 100.0)

    def test_demand_during_lead_time_formula(self):
        """demand_during_lead_time = daily_consumption × supplier_lead_time."""
        feat = build_stockout_features(self._raw(daily_consumption=10.0, supplier_lead_time=7))
        self.assertAlmostEqual(feat["demand_during_lead_time"], 70.0)

    def test_coverage_ratio_sufficient_stock(self):
        feat = build_stockout_features(
            self._raw(current_quantity=200.0, daily_consumption=10.0, supplier_lead_time=7)
        )
        # available=200, lead_need=70 → ratio≈2.857
        self.assertGreater(feat["coverage_ratio"], 1.0)

    def test_coverage_ratio_zero_lead_demand(self):
        """When lead-time demand is near-zero, coverage_ratio should be 1.0."""
        feat = build_stockout_features(
            self._raw(daily_consumption=0.0, supplier_lead_time=0)
        )
        self.assertAlmostEqual(feat["coverage_ratio"], 1.0)

    def test_days_until_stockout_calculated_correctly(self):
        feat = build_stockout_features(
            self._raw(current_quantity=50.0, daily_consumption=10.0)
        )
        # available=50, rate=10 → days=5
        self.assertAlmostEqual(feat["days_until_stockout"], 5.0)

    def test_days_until_stockout_is_none_for_zero_consumption(self):
        feat = build_stockout_features(
            self._raw(daily_consumption=0.0)
        )
        self.assertIsNone(feat["days_until_stockout"])

    def test_days_until_stockout_near_zero_consumption_returns_none(self):
        """Consumption at exactly NEAR_ZERO_CONSUMPTION threshold should yield None."""
        feat = build_stockout_features(
            self._raw(daily_consumption=NEAR_ZERO_CONSUMPTION)
        )
        self.assertIsNone(feat["days_until_stockout"])

    def test_pending_orders_included_in_available(self):
        feat = build_stockout_features(
            self._raw(current_quantity=10.0, pending_purchase_orders=90.0)
        )
        self.assertAlmostEqual(feat["available_quantity"], 100.0)

    def test_incoming_transfers_included_in_available(self):
        feat = build_stockout_features(
            self._raw(current_quantity=10.0, incoming_transfers=90.0)
        )
        self.assertAlmostEqual(feat["available_quantity"], 100.0)

    def test_missing_key_raises_value_error(self):
        data = self._raw()
        data.pop("daily_consumption")
        with self.assertRaises(ValueError):
            build_stockout_features(data)

    def test_negative_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            build_stockout_features(self._raw(current_quantity=-1.0))

    def test_non_finite_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            build_stockout_features(self._raw(current_quantity=float("inf")))

    def test_nan_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            build_stockout_features(self._raw(daily_consumption=float("nan")))

    def test_original_inputs_preserved_in_output(self):
        raw = self._raw()
        feat = build_stockout_features(raw)
        for key in ("current_quantity", "predicted_demand", "daily_consumption",
                    "supplier_lead_time", "pending_purchase_orders", "incoming_transfers"):
            self.assertIn(key, feat)

    def test_zero_all_inputs_no_crash(self):
        """All-zero inputs must not raise; days_until_stockout=None, coverage_ratio=1.0."""
        feat = build_stockout_features(self._raw(
            current_quantity=0.0, predicted_demand=0.0, daily_consumption=0.0,
            supplier_lead_time=0, pending_purchase_orders=0.0, incoming_transfers=0.0,
        ))
        self.assertIsNone(feat["days_until_stockout"])
        self.assertAlmostEqual(feat["coverage_ratio"], 1.0)


# ── Inference Tests ─────────────────────────────────────────────────────────


class TestStockoutPredictor(unittest.TestCase):
    """Tests for StockoutPredictor.predict inference contract."""

    def setUp(self):
        self.predictor = StockoutPredictor()

    def _predict(self, **overrides) -> dict:
        return self.predictor.predict(_make_request(**overrides))

    # ── Sufficient stock ────────────────────────────────────────────────────

    def test_sufficient_stock_low_risk(self):
        """
        200 units available, 70 lead-time need → coverage_ratio ≈ 2.86 ≥ 1.5 → LOW.
        (100/70 ≈ 1.43 which is below COVERAGE_MODERATE_THRESHOLD=1.5 → MODERATE.)
        """
        result = self._predict(
            current_quantity=200.0,
            daily_consumption=10.0,
            supplier_lead_time=7,
        )
        self.assertFalse(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.LOW)

    # ── Stockout within supplier lead time ──────────────────────────────────

    def test_stockout_within_lead_time_high_risk(self):
        """
        Available=60, lead_need=70 → stockout.
        coverage_ratio = 60/70 ≈ 0.857 >= COVERAGE_CRITICAL_THRESHOLD → HIGH.
        """
        result = self._predict(
            current_quantity=60.0,
            daily_consumption=10.0,
            supplier_lead_time=7,
            pending_purchase_orders=0.0,
            incoming_transfers=0.0,
        )
        self.assertTrue(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.HIGH)

    # ── Imminent / zero-stock critical case ─────────────────────────────────

    def test_zero_stock_critical_risk(self):
        """
        0 units available, 70 lead-time need → stockout.
        coverage_ratio = 0 < COVERAGE_CRITICAL_THRESHOLD → CRITICAL.
        """
        result = self._predict(
            current_quantity=0.0,
            daily_consumption=10.0,
            supplier_lead_time=7,
        )
        self.assertTrue(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.CRITICAL)

    def test_near_zero_stock_critical_risk(self):
        """Tiny stock, large lead need → CRITICAL."""
        result = self._predict(
            current_quantity=1.0,
            daily_consumption=10.0,
            supplier_lead_time=14,
        )
        # available=1, lead_need=140 → ratio≈0.007 < 0.5 → CRITICAL
        self.assertTrue(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.CRITICAL)

    # ── Pending purchase orders ──────────────────────────────────────────────

    def test_pending_purchase_orders_prevent_stockout(self):
        """POs in-flight count towards available stock."""
        result = self._predict(
            current_quantity=10.0,
            pending_purchase_orders=100.0,
            daily_consumption=10.0,
            supplier_lead_time=7,
        )
        # available=110, lead_need=70 → no stockout
        self.assertFalse(result["stockout_predicted"])

    def test_pending_purchase_orders_reduce_days_until_stockout(self):
        result = self._predict(
            current_quantity=50.0,
            pending_purchase_orders=50.0,
            daily_consumption=10.0,
            supplier_lead_time=5,
        )
        # available=100, rate=10 → days=10
        self.assertAlmostEqual(result["days_until_stockout"], 10.0)

    # ── Incoming transfers ───────────────────────────────────────────────────

    def test_incoming_transfers_prevent_stockout(self):
        """In-transit units from another facility count towards available stock."""
        result = self._predict(
            current_quantity=5.0,
            incoming_transfers=95.0,
            daily_consumption=10.0,
            supplier_lead_time=7,
        )
        # available=100, lead_need=70 → no stockout
        self.assertFalse(result["stockout_predicted"])

    # ── Zero consumption ─────────────────────────────────────────────────────

    def test_zero_consumption_no_stockout(self):
        """
        Zero daily consumption → lead_need=0 (near-zero) → coverage_ratio=1.0.
        1.0 < COVERAGE_MODERATE_THRESHOLD (1.5) → MODERATE.
        No stockout is predicted (0 is not < 0), but the item is still at amber.
        """
        result = self._predict(
            current_quantity=0.0,
            daily_consumption=0.0,
            supplier_lead_time=7,
        )
        self.assertFalse(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.MODERATE)

    def test_zero_consumption_days_until_stockout_is_none(self):
        result = self._predict(
            current_quantity=100.0,
            daily_consumption=0.0,
            supplier_lead_time=7,
        )
        self.assertIsNone(result["days_until_stockout"])

    # ── Lead time edge cases ─────────────────────────────────────────────────

    def test_zero_lead_time_no_stockout(self):
        """
        Zero supplier_lead_time → lead_need = daily_consumption × 0 = 0 (near-zero).
        coverage_ratio = 1.0 (lead-time window is instant) < COVERAGE_MODERATE_THRESHOLD → MODERATE.
        A LOW result requires coverage_ratio ≥ 1.5 (plenty of buffer above lead-time need).
        """
        result = self._predict(
            current_quantity=0.0,
            daily_consumption=10.0,
            supplier_lead_time=0,
        )
        self.assertFalse(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.MODERATE)

    def test_moderate_risk_boundary(self):
        """
        No stockout but coverage_ratio just below COVERAGE_MODERATE_THRESHOLD → MODERATE.
        available = 100, lead_need = 100 → ratio = 1.0 < COVERAGE_MODERATE_THRESHOLD (1.5).
        """
        result = self._predict(
            current_quantity=100.0,
            daily_consumption=10.0,
            supplier_lead_time=10,  # lead_need = 100
        )
        self.assertFalse(result["stockout_predicted"])
        self.assertEqual(result["risk_level"], RiskLevel.MODERATE)

    # ── Invalid inputs ───────────────────────────────────────────────────────

    def test_negative_current_quantity_raises(self):
        with self.assertRaises(ValidationError):
            self._predict(current_quantity=-1.0)

    def test_negative_daily_consumption_raises(self):
        with self.assertRaises(ValidationError):
            self._predict(daily_consumption=-5.0)

    def test_negative_pending_orders_raises(self):
        with self.assertRaises(ValidationError):
            self._predict(pending_purchase_orders=-10.0)

    def test_invalid_uuid_raises(self):
        with self.assertRaises(ValidationError):
            self._predict(facility_id="not-a-uuid")

    # ── Response schema validation ───────────────────────────────────────────

    def test_response_has_required_keys(self):
        result = self._predict()
        required_keys = {
            "success", "prediction_id", "facility_id", "item_id",
            "model_version", "generated_at", "stockout_predicted",
            "risk_level", "days_until_stockout", "available_quantity",
            "demand_during_lead_time", "coverage_ratio",
        }
        self.assertTrue(required_keys.issubset(result.keys()))

    def test_response_success_is_true(self):
        result = self._predict()
        self.assertTrue(result["success"])

    def test_response_prediction_id_is_uuid_v4(self):
        result = self._predict()
        self.assertTrue(is_valid_uuid_v4(result["prediction_id"]))

    def test_response_generated_at_is_utc_iso8601(self):
        result = self._predict()
        self.assertTrue(is_valid_utc_iso8601(result["generated_at"]))

    def test_response_model_version_matches_config(self):
        result = self._predict()
        self.assertEqual(result["model_version"], DEFAULT_MODEL_VERSION)

    def test_response_risk_level_is_canonical_string(self):
        result = self._predict()
        self.assertIn(result["risk_level"], [rl.value for rl in RiskLevel])

    def test_response_facility_and_item_ids_preserved(self):
        result = self._predict()
        self.assertEqual(result["facility_id"], FACILITY_ID)
        self.assertEqual(result["item_id"], ITEM_ID)

    def test_response_available_quantity_non_negative(self):
        result = self._predict()
        self.assertGreaterEqual(result["available_quantity"], 0.0)

    def test_response_demand_during_lead_time_non_negative(self):
        result = self._predict()
        self.assertGreaterEqual(result["demand_during_lead_time"], 0.0)

    # ── Determinism ──────────────────────────────────────────────────────────

    def test_deterministic_repeated_prediction(self):
        """Repeated calls with identical inputs must produce identical logical outputs."""
        req = _make_request()
        r1 = self.predictor.predict(req)
        r2 = self.predictor.predict(req)
        # Logic fields (not timestamps or IDs) must be identical.
        for key in ("stockout_predicted", "risk_level", "available_quantity",
                    "demand_during_lead_time", "coverage_ratio", "days_until_stockout"):
            self.assertEqual(r1[key], r2[key], msg=f"Mismatch on key '{key}'")

    def test_deterministic_across_predictor_instances(self):
        """Two fresh predictors must produce the same analytical result."""
        req = _make_request()
        r1 = StockoutPredictor().predict(req)
        r2 = StockoutPredictor().predict(req)
        for key in ("stockout_predicted", "risk_level", "coverage_ratio"):
            self.assertEqual(r1[key], r2[key])

    # ── Placeholder backward compatibility ───────────────────────────────────

    def test_placeholder_backward_compatibility(self):
        result = placeholder()
        self.assertEqual(result["status"], "placeholder")
        self.assertEqual(result["module"], "stockout_prediction.predict")

    # ── StockoutPredictionRequest object accepted directly ────────────────────

    def test_predict_accepts_request_object(self):
        request = StockoutPredictionRequest.model_validate(_make_request())
        result = self.predictor.predict(request)
        self.assertIn("stockout_predicted", result)


# ── Training Pipeline Tests ──────────────────────────────────────────────────


class TestStockoutTrainingPipeline(unittest.TestCase):
    """Tests for StockoutCoverageForecaster and train_stockout_pipeline."""

    def _records(self, n: int = 3) -> list:
        return [_make_request() for _ in range(n)]

    def test_fit_marks_forecaster_as_fitted(self):
        model = StockoutCoverageForecaster()
        self.assertFalse(model.is_fitted)
        model.fit(self._records())
        self.assertTrue(model.is_fitted)

    def test_predict_before_fit_raises_runtime_error(self):
        model = StockoutCoverageForecaster()
        with self.assertRaises(RuntimeError):
            model.predict(self._records())

    def test_predict_returns_feature_dicts(self):
        records = self._records(2)
        model = StockoutCoverageForecaster()
        model.fit(records)
        results = model.predict(records)
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn("available_quantity", result)
            self.assertIn("demand_during_lead_time", result)
            self.assertIn("coverage_ratio", result)

    def test_train_pipeline_returns_model_and_metadata(self):
        records = self._records(5)
        model, meta = train_stockout_pipeline(records)
        self.assertTrue(model.is_fitted)
        self.assertEqual(meta["sample_size"], 5)
        self.assertEqual(meta["method"], "deterministic_coverage_rule")
        self.assertIn("model_version", meta)

    def test_fit_with_empty_records_raises(self):
        with self.assertRaises(ValueError):
            StockoutCoverageForecaster().fit([])

    def test_fit_accepts_dataframe(self):
        """fit() should also accept a DataFrame (as used by train_stockout_pipeline)."""
        import pandas as pd
        records = self._records(3)
        from ai.stockout_prediction.data import validate_and_load_records
        frame = validate_and_load_records(records)
        model = StockoutCoverageForecaster()
        model.fit(frame)
        self.assertTrue(model.is_fitted)


# ── Evaluation Tests ─────────────────────────────────────────────────────────


class TestEvaluateStockoutPredictions(unittest.TestCase):
    """Tests for evaluate_stockout_predictions against real classification metrics."""

    def _stockout_record(self) -> dict:
        """Returns a record that WILL trigger stockout (available < lead_need)."""
        return _make_request(
            current_quantity=10.0,
            daily_consumption=10.0,
            supplier_lead_time=7,   # lead_need=70, available=10
            pending_purchase_orders=0.0,
            incoming_transfers=0.0,
        )

    def _safe_record(self) -> dict:
        """Returns a record that will NOT trigger stockout."""
        return _make_request(
            current_quantity=200.0,
            daily_consumption=10.0,
            supplier_lead_time=7,   # lead_need=70, available=200
        )

    def test_perfect_predictions_f1_is_one(self):
        records = [self._stockout_record(), self._safe_record()]
        y_true = [1, 0]  # stockout, then safe
        metrics = evaluate_stockout_predictions(records, y_true)
        self.assertAlmostEqual(metrics["f1"], 1.0)
        self.assertAlmostEqual(metrics["accuracy"], 1.0)

    def test_wrong_labels_f1_is_zero(self):
        records = [self._safe_record(), self._safe_record()]
        y_true = [1, 1]  # both labelled as stockout, but rule predicts 0
        metrics = evaluate_stockout_predictions(records, y_true)
        self.assertAlmostEqual(metrics["f1"], 0.0)

    def test_length_mismatch_raises_value_error(self):
        records = [self._stockout_record(), self._safe_record()]
        with self.assertRaises(ValueError):
            evaluate_stockout_predictions(records, [1])  # wrong length

    def test_returns_all_expected_metric_keys(self):
        records = [self._stockout_record()]
        metrics = evaluate_stockout_predictions(records, [1])
        for key in ("accuracy", "precision", "recall", "f1",
                    "true_positives", "false_positives",
                    "true_negatives", "false_negatives"):
            self.assertIn(key, metrics)


# ── Data Layer Tests ─────────────────────────────────────────────────────────


class TestValidateAndLoadRecords(unittest.TestCase):
    """Tests for the data loading / normalisation layer."""

    def test_valid_records_produce_dataframe(self):
        import pandas as pd
        records = [_make_request(), _make_request()]
        frame = validate_and_load_records(records)
        self.assertIsInstance(frame, pd.DataFrame)
        self.assertEqual(len(frame), 2)

    def test_empty_records_raise_value_error(self):
        with self.assertRaises(ValueError):
            validate_and_load_records([])

    def test_invalid_record_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            validate_and_load_records([_make_request(current_quantity=-1.0)])

    def test_all_numeric_columns_present(self):
        records = [_make_request()]
        frame = validate_and_load_records(records)
        for col in ("current_quantity", "predicted_demand", "daily_consumption",
                    "supplier_lead_time", "pending_purchase_orders",
                    "incoming_transfers"):
            self.assertIn(col, frame.columns)


if __name__ == "__main__":
    unittest.main()
