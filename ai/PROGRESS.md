# Sanjeevani Grid - AI Subsystem Progress & Handoff Log

Persistent tracking document for Member 3 (`ai/member-3`) machine learning pipelines and intelligence subsystem.

---

## 1. Current Branch
- **Branch**: `ai/member-3`
- **Target Integration Branch**: `develop` (via Pull Request only)
- **Status**: Checked out on ai/member-3; Phase 1 implementation complete; checkpoint pending commit

---

## 2. Current Phase
- **Phase Status**: **Phase 1 — Shared Core Foundation — COMPLETE**

---

## 3. Completed Implementation

| File | Type | Description |
| :--- | :--- | :--- |
| [`ai/AGENTS.md`](./AGENTS.md) | Guidelines | Persistent operating rules, source of truth, boundaries, and ML quality standards |
| [`ai/common/types.py`](./common/types.py) | Types / Utility | Canonical `RiskLevel` enum, UUID v4 validation, and UTC ISO-8601 timestamp handlers |
| [`ai/common/metrics.py`](./common/metrics.py) | Math / Evaluation | Real forecasting (MAE, RMSE, MAPE, WAPE) and classification metrics (Brier, F1, accuracy) |
| [`ai/common/serialization.py`](./common/serialization.py) | Persistence | Joblib-based model artifact serialization (`save_artifact`, `load_artifact`) with auto-mkdir |
| [`ai/common/base_model.py`](./common/base_model.py) | Base Classes | Abstract interfaces for `BaseForecaster`, `BasePredictor`, and `BaseScorer` |
| [`ai/common/__init__.py`](./common/__init__.py) | Package Root | Clean public exports for all common foundation primitives |
| [`ai/tests/test_common.py`](./tests/test_common.py) | Unit Tests | 19 behavioral unit tests verifying lifecycle, persistence, edge-cases, and validators |

---

## 4. Validation Summary
- **Foundation Unit Tests**: 19 tests passed (`python -m unittest discover -s ai/tests -v`).
- **Placeholder Regression Test**: Passed (`test_ai_placeholders.py`).
- **Dependencies**: Zero packages installed; operated strictly on available environment.
- **Repository Boundaries**: Zero files outside Member 3 (`ai/`) touched or modified.

---

## 5. Key Implementation Decisions
1. **Canonical Risk Levels**: Defined `RiskLevel` (`low`, `moderate`, `high`, `critical`) inheriting from `StrEnum` to guarantee exact match with `docs/api/API_CONVENTIONS.md` (Section 5) and clean JSON/Pydantic serialization.
2. **UUID v4 Validation**: Enforced version-4 regex and byte parsing via `ensure_uuid_v4` and `is_valid_uuid_v4`, rejecting older UUID versions and malformed strings.
3. **UTC ISO-8601 Handling**: Enforced trailing `Z` or `+00:00` format via `ensure_utc_iso8601` and `now_utc_iso8601`, rejecting naive datetimes and non-UTC offsets.
4. **Forecasting Metrics**: Mathematical implementations of MAE, RMSE, MAPE, and WAPE with safe epsilon division and zero-actual edge case protection.
5. **Classification / Risk Metrics**: Analytical Brier score calculation (with $[0, 1]$ probability validation) and classification metrics with configurable `zero_division` parameter.
6. **Artifact Serialization**: Joblib serialization targeting `.joblib` artifacts with automatic parent directory creation, path resolution, and seamless fallback to pickle when joblib installation is pending.
7. **Base Abstractions**: Upgraded `BaseForecaster` to typed `abc.ABC` while preserving its original `fit` and `predict` contract, adding `BasePredictor` for inference validation and `BaseScorer` for composite scoring.

---

## 6. Phase 3 Completed Implementation — Stockout Prediction

| File | Type | Description |
| :--- | :--- | :--- |
| [`ai/stockout_prediction/config.py`](./stockout_prediction/config.py) | Config | Model version tag, NEAR_ZERO_CONSUMPTION guard, and documented risk-level coverage thresholds (`COVERAGE_CRITICAL_THRESHOLD=0.5`, `COVERAGE_MODERATE_THRESHOLD=1.5`) |
| [`ai/stockout_prediction/schema.py`](./stockout_prediction/schema.py) | Schema | Pydantic v2 request (6 documented inputs + UUIDs) and response (`generated_at`, `coverage_ratio`, canonical `RiskLevel`, UUID v4, UTC ISO-8601) |
| [`ai/stockout_prediction/features.py`](./stockout_prediction/features.py) | Features | Deterministic `build_stockout_features`: available quantity, demand_during_lead_time, coverage_ratio, days_until_stockout — division-by-zero safe |
| [`ai/stockout_prediction/data.py`](./stockout_prediction/data.py) | Data | Schema-validated record ingestion → clean `pd.DataFrame` with finite-value guard |
| [`ai/stockout_prediction/train.py`](./stockout_prediction/train.py) | Train | `StockoutCoverageForecaster(BaseForecaster)` — validation-based fit (no supervised target per spec); `train_stockout_pipeline` convenience entry point |
| [`ai/stockout_prediction/evaluate.py`](./stockout_prediction/evaluate.py) | Evaluate | `evaluate_stockout_predictions` using real `calculate_classification_metrics` from `ai/common/metrics` |
| [`ai/stockout_prediction/predict.py`](./stockout_prediction/predict.py) | Inference | `StockoutPredictor(BasePredictor)` — schema-validated inference, canonical `RiskLevel` assignment, `generated_at` UTC timestamp, `placeholder()` preserved |
| [`ai/tests/test_stockout_prediction.py`](./tests/test_stockout_prediction.py) | Tests | 77 focused unit tests across 5 test classes; all pass |

---

## 7. Phase 3 Validation Summary
- **Phase 3 Unit Tests**: 77 tests passed (`python -m unittest ai.tests.test_stockout_prediction -v`).
- **Full Suite (Phase 1 + Phase 2 + Phase 3)**: 110 tests passed (`python -m unittest discover -s ai/tests -v`).
- **Repository Boundaries**: Zero files outside `ai/` touched. Phase 2 untouched.
- **No fabricated metrics, probabilities, or confidence scores introduced.**
- **Python**: 3.14.3 (available as `python`).

---

## 8. Phase 3 Key Design Decisions

1. **Deterministic rule only**: The spec provides six inputs but no labelled stockout-event training target. Inventing a supervised target is forbidden by `ai/AGENTS.md`. The pipeline uses classical reorder-point theory; `fit()` validates records without learning weights.
2. **`demand_during_lead_time = daily_consumption × supplier_lead_time`**: The coverage need during restocking is computed from the consumption rate and lead time window. `predicted_demand` (Phase 2 output) is a separate field retained in the schema for upstream visibility but does not override the lead-time formula.
3. **`coverage_ratio` thresholds** (documented in `config.py`):
   - `< 0.5` while stockout predicted → `CRITICAL` (severely undercovered)
   - `≥ 0.5` while stockout predicted → `HIGH`
   - No stockout, `< 1.5` → `MODERATE` (approaching reorder point — conservative 50 % buffer)
   - No stockout, `≥ 1.5` → `LOW` (adequate buffer)
4. **`coverage_ratio = 1.0` when `demand_during_lead_time` is near-zero**: Prevents division-by-zero while correctly expressing that zero demand during lead time is fully covered. This saturates to MODERATE (not LOW) because ratio=1.0 is still below COVERAGE_MODERATE_THRESHOLD.
5. **`days_until_stockout = None` when `daily_consumption ≤ NEAR_ZERO_CONSUMPTION`**: Semantically correct — if nothing is being consumed, depletion is undefined, not infinite.
6. **`generated_at` + `coverage_ratio` added to response schema**: Missing from the previous agent's implementation. `generated_at` matches Phase 2 conventions; `coverage_ratio` provides full observability into the risk scoring decision.

---

## 9. Phase 4 Completed Implementation — Expiry Prediction & Anomaly Detection

### A. Expiry Prediction (`ai/expiry_prediction/`)
| File | Type | Description |
| :--- | :--- | :--- |
| [`ai/expiry_prediction/config.py`](./expiry_prediction/config.py) | Config | Model version, near-zero threshold, and explicit implementation-chosen wastage risk ratio cutoffs |
| [`ai/expiry_prediction/schema.py`](./expiry_prediction/schema.py) | Schema | Pydantic v2 schemas for documented inputs (batch expiry, stock, current/forecast consumption) and outputs (unused quantity, wastage risk, financial loss) |
| [`ai/expiry_prediction/features.py`](./expiry_prediction/features.py) | Features | Leak-free shelf-life, projected consumption, unused quantity, wastage ratio, and financial loss |
| [`ai/expiry_prediction/data.py`](./expiry_prediction/data.py) | Data | Schema validation, record normalization into pandas DataFrame with finite-value checks |
| [`ai/expiry_prediction/train.py`](./expiry_prediction/train.py) | Train | `ExpiryCoverageForecaster(BaseForecaster)` lifecycle and convenience `train_expiry_pipeline` |
| [`ai/expiry_prediction/evaluate.py`](./expiry_prediction/evaluate.py) | Evaluate | `evaluate_expiry_predictions` reusing `ai.common.metrics.calculate_classification_metrics` |
| [`ai/expiry_prediction/predict.py`](./expiry_prediction/predict.py) | Inference | `ExpiryPredictor(BasePredictor)` inference service assigning canonical `RiskLevel` |
| [`ai/expiry_prediction/__init__.py`](./expiry_prediction/__init__.py) | Package | Clean public exports |
| [`ai/tests/test_expiry_prediction.py`](./tests/test_expiry_prediction.py) | Tests | 32 focused unit tests across 6 test classes |

### B. Anomaly Detection (`ai/anomaly_detection/`)
| File | Type | Description |
| :--- | :--- | :--- |
| [`ai/anomaly_detection/config.py`](./anomaly_detection/config.py) | Config | Documented target types, normal MAD consistency scale (1.4826), and implementation-chosen z-score thresholds |
| [`ai/anomaly_detection/schema.py`](./anomaly_detection/schema.py) | Schema | Pydantic v2 schemas for targets (sudden decrease, abnormal consumption, unusual disease, attendance drop, suspicious adjustment) |
| [`ai/anomaly_detection/features.py`](./anomaly_detection/features.py) | Features | Robust z-score computation using Median and MAD, zero-variance handling, and surge/drop directionality |
| [`ai/anomaly_detection/data.py`](./anomaly_detection/data.py) | Data | Normalization and validation for anomaly records |
| [`ai/anomaly_detection/train.py`](./anomaly_detection/train.py) | Train | `RobustZScoreAnomalyDetector(BaseForecaster)` baseline fitting, serialization, and batch inference |
| [`ai/anomaly_detection/evaluate.py`](./anomaly_detection/evaluate.py) | Evaluate | `evaluate_anomaly_predictions` and `evaluate_records_anomaly` reusing common metrics |
| [`ai/anomaly_detection/predict.py`](./anomaly_detection/predict.py) | Inference | `AnomalyDetectorPredictor(BasePredictor)` inference service with canonical `RiskLevel` mapping |
| [`ai/anomaly_detection/__init__.py`](./anomaly_detection/__init__.py) | Package | Clean public exports |
| [`ai/tests/test_anomaly_detection.py`](./tests/test_anomaly_detection.py) | Tests | 29 focused unit tests across 6 test classes |

---

## 10. Phase 4 Validation Summary
- **Phase 4 Expiry Tests**: 32 tests passed (`python -m unittest ai.tests.test_expiry_prediction -v`).
- **Phase 4 Anomaly Tests**: 29 tests passed (`python -m unittest ai.tests.test_anomaly_detection -v`).
- **Full AI Suite (Phases 1–4)**: 171 tests passed (`python -m unittest discover -s ai/tests -v`).
- **Repository Boundaries**: Strictly confined to `ai/`. Zero files modified outside `ai/`.
- **Zero fabricated labels, probabilities, or confidence scores.**

---

## 11. Phase 4 Key Implementation Assumptions

1. **Expiry Prediction — Primary burn rate**: `effective_daily_rate` uses `forecast_consumption` (from Phase 2) as the primary forward-looking daily rate if positive, falling back to `current_consumption` if forecast consumption is 0.
2. **Expiry Prediction — Wastage Risk Thresholds**: `wastage_ratio = likely_unused_quantity / batch_stock`. Thresholds `CRITICAL >= 0.50`, `HIGH >= 0.20`, `MODERATE >= 0.05`, `LOW < 0.05` are implementation defaults documented in `config.py` since the source documents specify no numeric boundaries.
3. **Anomaly Detection — Robust Z-score approach**: Robust z-score (using Median and scaled MAD with $k=1.4826$) was intentionally selected as one of the three documented approaches in the Member 3 source of truth, alongside Isolation Forest and Local Outlier Factor.
4. **Anomaly Detection — Anomaly & Risk Thresholds**: Thresholds $|Z| \ge 4.5$ (`CRITICAL`), $|Z| \ge 3.0$ (`HIGH`/anomaly), $|Z| \ge 2.0$ (`MODERATE`), and $|Z| < 2.0$ (`LOW`) are implementation defaults documented in `config.py`.

---

## 12. Next Phase
- **Target**: **Phase 5** (per project roadmap)

---

## 13. Important Safety Rules
1. Work exclusively within `ai/` on branch `ai/member-3`.
2. Do not modify `frontend/`, `backend/`, `infra/`, `federated/`, `optimization/`, or any other team member's files.
3. Treat project Markdown specifications in `docs/` and root `README.md` as the absolute source of truth.
4. Never fabricate metrics, confidence intervals, or model behavior.
5. Checkpoint progress and verify test passes before transitioning across major phases.
