# Member 3 - AI & Machine Learning Guide

- **Assigned Git Branch**: `ai/member-3`
- **Target Integration Branch**: `develop`
- **Primary Working Directory**: `ai/`

## Technology Stack

- Python 3.11 / 3.12 / 3.13
- Scikit-learn, XGBoost, LightGBM, PyTorch
- Pandas, NumPy, SciPy
- MLflow tracking

## Workflow

1. Check out your branch:
   ```bash
   git checkout -b ai/member-3 develop
   ```
2. Setup environment:
   ```bash
   cd ai
   pip install -r requirements.txt
   ```
3. Implement models within their respective folders (`demand_forecasting/`, `stockout_prediction/`, etc.).
4. Use standard interfaces:
   - `data.py`: data loading
   - `features.py`: engineering & scaling
   - `train.py`: model fit & artifact output
   - `evaluate.py`: validation metrics
   - `predict.py`: inference contract
5. Verify unit tests via `pytest tests/` before opening PR to `develop`.
