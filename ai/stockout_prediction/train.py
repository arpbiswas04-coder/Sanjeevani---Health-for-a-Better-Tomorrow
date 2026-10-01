"""
Sanjeevani Grid - Stockout Prediction Training Pipeline
ai/stockout_prediction/train.py

Fits the documented deterministic stock-coverage rule model.

Design note (per ai/AGENTS.md Section 6 quality rules):
  The Member 3 specification provides six stockout inputs but does NOT supply
  a labelled training target (e.g. "did this SKU actually stock out?").
  Inventing a supervised learning target or fabricating learned weights is
  forbidden by ai/AGENTS.md.

  This module therefore implements a 'fit' step that:
    1. Validates all training records against the schema.
    2. Marks the forecaster as fitted (enabling safe batch predict calls).

  The scoring rule itself lives in features.py and predict.py and is based
  on classical reorder-point theory — fully deterministic and explainable.
  When labelled stockout event data becomes available, evaluate.py can be
  used to measure real classification performance against this rule.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

from ai.common.base_model import BaseForecaster
from ai.stockout_prediction.data import validate_and_load_records
from ai.stockout_prediction.features import build_stockout_features


class StockoutCoverageForecaster(BaseForecaster):
    """
    Deterministic rule-based stockout risk model.

    Inherits BaseForecaster so that it integrates with the shared serialization
    and lifecycle contract.  fit() validates input records; predict() applies
    build_stockout_features to each row.
    """

    def __init__(self, model_version: str = "stockout_coverage_v1.0.0") -> None:
        super().__init__(model_name="StockoutCoverageForecaster")
        self.model_version = model_version

    def fit(
        self,
        X: Any,
        y: Any = None,
        **kwargs: Any,
    ) -> "StockoutCoverageForecaster":
        """
        Validate training records and mark the forecaster as fitted.

        Parameters
        ----------
        X : DataFrame or Iterable[dict]
            Collection of point-in-time stockout records.  Validates each
            record against StockoutPredictionRequest schema.
        y : ignored
            No supervised target is available per the documented specification.

        Returns
        -------
        self
        """
        if X is not None:
            records: Iterable[Dict[str, Any]] = (
                X.to_dict(orient="records")
                if (hasattr(X, "to_dict") and hasattr(X, "columns"))
                else X
            )
            validate_and_load_records(records)
        self.is_fitted = True
        return self

    def predict(self, X: Any, **kwargs: Any) -> Any:
        """
        Apply the coverage rule to each record in X.

        Parameters
        ----------
        X : DataFrame or Iterable[dict]
            Collection of validated stockout input records.

        Returns
        -------
        list[dict]
            One feature dict per record (output of build_stockout_features).

        Raises
        ------
        RuntimeError
            If predict is called before fit.
        """
        if not self.is_fitted:
            raise RuntimeError(
                "StockoutCoverageForecaster.predict() called before fit()."
            )
        rows: Iterable[Dict[str, Any]] = (
            X.to_dict(orient="records")
            if (hasattr(X, "to_dict") and hasattr(X, "columns"))
            else X
        )
        return [build_stockout_features(row) for row in rows]


def train_stockout_pipeline(
    records: Any,
    save_path: Optional[Union[str, Path]] = None,
) -> tuple:
    """
    Convenience entry point: validate → fit → optionally serialize.

    Returns
    -------
    (model, metadata_dict)
        model    : fitted StockoutCoverageForecaster
        metadata : dict with sample_size and method description
    """
    frame = validate_and_load_records(records)
    model = StockoutCoverageForecaster()
    model.fit(frame)
    if save_path is not None:
        model.save(save_path)
    return model, {
        "sample_size": len(frame),
        "method": "deterministic_coverage_rule",
        "model_version": model.model_version,
    }


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "stockout_prediction.train", "status": "placeholder"}
