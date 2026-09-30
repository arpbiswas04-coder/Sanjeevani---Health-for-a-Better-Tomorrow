"""
Sanjeevani Grid - Expiry Prediction Training Pipeline
ai/expiry_prediction/train.py

Defines the model training and fitting lifecycle for batch expiration prediction.

Design note (per ai/AGENTS.md Section 6):
  The Member 3 specification defines input features (batch expiry, batch stock,
  current consumption, forecast consumption) and outputs (likely unused quantity,
  wastage risk, estimated financial loss) but does NOT provide labelled historical
  batch spoilage targets. Inventing a supervised training target or fabricating
  learned weights is strictly forbidden.

  This module therefore implements `ExpiryCoverageForecaster` (inheriting from
  `BaseForecaster`) to provide the standard fit/predict/save/load interface,
  validating input data during `fit` and applying deterministic spoilage modeling
  during `predict`.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple, Union

from ai.common.base_model import BaseForecaster
from ai.expiry_prediction.config import DEFAULT_MODEL_VERSION
from ai.expiry_prediction.data import validate_and_load_expiry_records
from ai.expiry_prediction.features import build_expiry_features


class ExpiryCoverageForecaster(BaseForecaster):
    """
    Deterministic rule-based model for batch expiration and spoilage risk.

    Inherits from BaseForecaster for standard serialization and lifecycle.
    """

    def __init__(self, model_version: str = DEFAULT_MODEL_VERSION) -> None:
        super().__init__(model_name="ExpiryCoverageForecaster")
        self.model_version = model_version

    def fit(
        self,
        X: Any,
        y: Any = None,
        **kwargs: Any,
    ) -> "ExpiryCoverageForecaster":
        """
        Validate input batch records and set fitted state.

        Parameters
        ----------
        X : DataFrame or Iterable[dict]
            Raw or structured batch records.
        y : ignored
            No supervised target in specification.

        Returns
        -------
        self
        """
        if X is not None:
            if hasattr(X, "to_dict") and hasattr(X, "columns"):
                records = X.to_dict(orient="records")
            else:
                records = X
            validate_and_load_expiry_records(records)

        self.is_fitted = True
        return self

    def predict(self, X: Any, **kwargs: Any) -> Any:
        """
        Apply expiry feature extraction to each record.

        Parameters
        ----------
        X : DataFrame or Iterable[dict]
            Records to evaluate.

        Returns
        -------
        list[dict]
            Computed feature mappings.
        """
        if not self.is_fitted:
            raise RuntimeError("ExpiryCoverageForecaster must be fitted before predict.")

        if hasattr(X, "to_dict") and hasattr(X, "columns"):
            rows: Iterable[Dict[str, Any]] = X.to_dict(orient="records")
        else:
            rows = X

        return [build_expiry_features(row) for row in rows]


def train_expiry_pipeline(
    records: Any,
    save_path: Optional[Union[str, Path]] = None,
) -> Tuple[ExpiryCoverageForecaster, Dict[str, Any]]:
    """
    Convenience pipeline entry point: validate -> fit -> optionally save.
    """
    frame = validate_and_load_expiry_records(records)
    model = ExpiryCoverageForecaster()
    model.fit(frame)
    if save_path is not None:
        model.save(save_path)
    return model, {
        "sample_size": len(frame),
        "method": "deterministic_expiry_coverage",
        "model_version": model.model_version,
    }


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "expiry_prediction.train", "status": "placeholder"}
