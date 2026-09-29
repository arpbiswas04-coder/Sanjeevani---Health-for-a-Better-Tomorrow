# Sanjeevani Grid - AI & Machine Learning Subsystem

This directory contains the predictive models, analytics pipelines, and feature engineering tasks owned by **Member 3** (`ai/member-3`).

## Subsystem Architecture

Each model pipeline is structured consistently with isolated components:
- `data.py`: Ingestion, loading, and cleaning of raw data sources.
- `features.py`: Feature extraction, encoding, scaling, and lag generation.
- `train.py`: Model training, hyperparameter optimization, and artifact serialization.
- `evaluate.py`: Performance metrics computation, backtesting, and validation reports.
- `predict.py`: Inference service interface for live and batch predictions.
- `config.py`: Hyperparameters, model paths, and pipeline configurations.
- `schema.py`: Input/output Pydantic schemas validating inference contracts.

## Model Domains

1. `demand_forecasting`: Medicine and medical equipment consumption forecasting.
2. `stockout_prediction`: Early warning system for low stock and supply disruptions.
3. `expiry_prediction`: Drug expiration horizon and batch spoilage risk.
4. `patient_forecasting`: Inpatient/outpatient influx rate predictions.
5. `bed_forecasting`: ICU and general ward bed occupancy projections.
6. `workforce_forecasting`: Doctor and nurse staffing requirement modeling.
7. `disease_intelligence`: Epidemiological surge detection and geospatial clusters.
8. `anomaly_detection`: Unusual consumption or emergency spikes.
9. `risk_scoring`: Composite resilience and risk assessment for healthcare facilities.
10. `explainability`: SHAP/LIME feature attribution explanations.
11. `model_monitoring`: Drift detection, performance tracking, and retraining triggers.

## Local Setup

```bash
cd ai
pip install -r requirements.txt
pytest tests/
```
