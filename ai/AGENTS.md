# Sanjeevani Grid - AI Subsystem Agent Guidelines (`ai/AGENTS.md`)

This document defines the persistent operating rules and engineering standards for AI agents and contributors working on the Sanjeevani Grid AI subsystem.

---

## 1. Source of Truth & Conflict Resolution
- The repository documentation (`docs/team/MEMBER_3_AI.md`, `docs/team/INTEGRATION_GUIDE.md`, `docs/architecture/ARCHITECTURE.md`, `README.md`, and `ai/README.md`) is the absolute source of truth.
- **Conflict Rule**: If any user request, prompt, or proposed modification conflicts with the repository Markdown specifications, **STOP and ask the user for clarification** before proceeding.
- **Inspect Before Modifying**: The agent must always inspect existing files, interfaces, schemas, and tests before making any changes.

---

## 2. Member 3 Scope & Ownership
- **Owner**: Member 3 (`ai/member-3`).
- **Core Domain**: AI/ML predictive modeling, time-series forecasting, risk scoring, disease intelligence, explainability using the documented SHAP approach, and model monitoring.
- **Assigned Git Branch**: `ai/member-3`.
- **Target Integration Branch**: `develop` (via Pull Request only).
- **Out of Scope (Owned by other members)**:
  - Frontend SPA (`frontend/` - Member 1).
  - Backend API, database models, CRUD, auth (`backend/` - Member 2).
  - Infrastructure, Docker, NGINX, Prometheus/Grafana (`infra/` - Member 4).
  - Federated edge learning coordinator and clients (`federated/` - Member 4).
  - Operations Research & optimization solvers (`optimization/` - Member 4).

---

## 3. Allowed Directory Boundaries & Modification Restrictions
- **Allowed Directory**: Work strictly within `ai/`.
- **Forbidden Modifications**: **DO NOT** modify `frontend/`, `backend/`, `infra/`, `federated/`, `optimization/`, root orchestration files (`docker-compose.yml`, `Makefile`, `.env.example`, `.gitignore`, `CONTRIBUTING.md`), or any other team member's work unless explicitly authorized in writing by the user.

---

## 4. Documented Technologies & Dependencies
Adhere strictly to the documented technology stack. Do not invent or add unapproved dependencies:
- **Python Versions**: Python 3.11 / 3.12 / 3.13.
- **Documented Dependencies** (per `ai/requirements.txt` and repository docs):
  - `numpy>=1.26.0,<3.0.0`
  - `pandas>=2.2.0,<3.0.0`
  - `scikit-learn>=1.5.0,<2.0.0`
  - `scipy>=1.13.0,<2.0.0`
  - `pydantic>=2.10.0,<3.0.0`
  - `mlflow>=2.19.0,<3.0.0`
  - `joblib>=1.4.0,<2.0.0`
  - `pytest>=8.3.0,<9.0.0`
  - Supported ML ecosystem packages specified in docs: XGBoost, LightGBM, PyTorch.
- **Package Management Rule**: Do not install packages or modify `ai/requirements.txt` without explicit user instruction.

---

## 5. Standardized Module Structure
Every predictive pipeline within `ai/` (`demand_forecasting`, `stockout_prediction`, `expiry_prediction`, `patient_forecasting`, `bed_forecasting`, `workforce_forecasting`, `disease_intelligence`, `anomaly_detection`, `risk_scoring`, `explainability`, `model_monitoring`) must strictly follow the uniform component architecture:
- `data.py`: Ingestion, loading, validation, and cleaning of raw data sources.
- `features.py`: Feature extraction, encoding, scaling, transformations, and lag generation.
- `train.py`: Model fitting, hyperparameter tuning, cross-validation, and artifact serialization.
- `evaluate.py`: Performance metrics computation, backtesting, and validation reports.
- `predict.py`: Inference service contract for real-time and batch predictions.
- `config.py`: Hyperparameters, model storage paths, and pipeline configurations.
- `schema.py`: Input/output Pydantic models enforcing strict data contracts.
- `common/`: Shared base classes (`BaseForecaster`) and reusable utility functions.

---

## 6. Machine Learning Quality Rules
- **Real Evaluation**: Evaluation metrics (MAE, RMSE, MAPE, ROC-AUC, F1, etc.) must be genuinely computed against holdout validation or backtest sets. Never fabricate metrics or reports.
- **No Fabricated Confidence**: Prediction intervals and confidence scores must derive from actual probabilistic estimates, quantile regressions, or empirical residuals—never hardcoded placeholders or arbitrary mock values.
- **Reproducible Inference**: Fix random seeds (`random_state`), maintain deterministic pipelines, and serialize versioned model artifacts using MLflow and joblib.
- **Robustness**: Explicitly handle missing values, out-of-vocabulary categories, NaNs, and unexpected input boundaries.

---

## 7. Prediction, Schema, & Integration Contracts
- All inference endpoints in `predict.py` must validate inputs against `schema.py` Pydantic models before computing predictions.
- Outputs must return schema-validated, typed responses suitable for backend API consumption.
- Keep the boundary clean: AI pipelines function as inference engines; they do not access database drivers directly or execute backend business logic.

---

## 8. Testing Requirements
- Maintain unit and integration tests under `ai/tests/`.
- Tests must cover:
  - Pydantic schema validation (valid inputs, invalid inputs, edge values).
  - Feature engineering correctness and deterministic output.
  - Model training runs and artifact generation.
  - Predictor inference contracts, return structures, and error handling.
- Verify tests via `pytest tests/` (or `pytest ai/tests/`) before submitting changes.

---

## 9. Git Safety Rules
- Confirm current branch is `ai/member-3` before making changes.
- Never commit directly to `main` or `develop`.
- Never force push (`git push --force`).
- Do not commit or push without user instruction.
- Integration into `develop` occurs strictly via Pull Requests with passing CI checks.
