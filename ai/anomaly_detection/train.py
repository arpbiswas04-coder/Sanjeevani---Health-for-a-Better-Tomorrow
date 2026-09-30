"""
Sanjeevani Grid - Anomaly Detection Model Training
ai/anomaly_detection/train.py

Implements baseline estimation and artifact serialization for the robust
statistical anomaly detection pipeline.

Design note (per ai/AGENTS.md Section 6):
  Anomaly detection operates in an unsupervised/statistical setting using robust
  z-scores (with median and MAD) as specified by the Member 3 blueprint.
  `RobustZScoreAnomalyDetector` inherits from `BaseForecaster` for standard
  lifecycle and serialization compliance.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple, Union
import numpy as np

from ai.common.base_model import BaseForecaster
from ai.anomaly_detection.config import (
    DEFAULT_MODEL_VERSION,
    DEFAULT_Z_THRESHOLD,
    MAD_NORMAL_SCALE,
)
from ai.anomaly_detection.features import compute_robust_zscore


class RobustZScoreAnomalyDetector(BaseForecaster):
    """
    Robust Z-Score Anomaly Detector based on historical Median and MAD.

    Inherits from BaseForecaster for standard serialization and persistence.
    """

    def __init__(
        self,
        z_threshold: float = DEFAULT_Z_THRESHOLD,
        model_version: str = DEFAULT_MODEL_VERSION,
    ) -> None:
        super().__init__(model_name="RobustZScoreAnomalyDetector")
        self.z_threshold = z_threshold
        self.model_version = model_version
        self.baseline_median: float = 0.0
        self.baseline_mad: float = 0.0
        self.scaled_mad: float = 0.0
        self.history_size: int = 0

    def fit(
        self,
        X: Any,
        y: Any = None,
        **kwargs: Any,
    ) -> "RobustZScoreAnomalyDetector":
        """
        Fit detector to historical training sequence.

        Parameters
        ----------
        X : Sequence[float] or DataFrame / dict
            Historical sequence representing normal operational baseline.
        y : ignored
            Unsupervised statistical method.

        Returns
        -------
        self
        """
        if isinstance(X, (list, tuple, np.ndarray)):
            arr = np.asarray(X, dtype=np.float64)
        elif hasattr(X, "to_numpy"):
            arr = X.to_numpy(dtype=np.float64).flatten()
        elif isinstance(X, dict) and "history" in X:
            arr = np.asarray(X["history"], dtype=np.float64)
        else:
            raise TypeError(f"Unsupported data type for fitting anomaly detector: {type(X)}")

        if len(arr) < 3:
            raise ValueError(f"Training history must contain at least 3 points; got {len(arr)}")
        if not np.isfinite(arr).all():
            raise ValueError("Training history contains non-finite values.")

        self.baseline_median = float(np.median(arr))
        abs_deviations = np.abs(arr - self.baseline_median)
        self.baseline_mad = float(np.median(abs_deviations))
        self.scaled_mad = float(self.baseline_mad * MAD_NORMAL_SCALE)
        self.history_size = len(arr)
        self.is_fitted = True

        return self

    def predict(self, X: Any, **kwargs: Any) -> Any:
        """
        Compute anomaly predictions for input values.

        Parameters
        ----------
        X : Sequence[float] or float
            Observation(s) to score.

        Returns
        -------
        list[dict]
            Computed feature mappings and anomaly classifications.
        """
        if not self.is_fitted:
            raise RuntimeError("RobustZScoreAnomalyDetector must be fitted before predict.")

        if isinstance(X, (int, float)):
            values = [float(X)]
        elif isinstance(X, (list, tuple, np.ndarray)):
            values = [float(v) for v in X]
        elif hasattr(X, "to_numpy"):
            values = [float(v) for v in X.to_numpy().flatten()]
        else:
            raise TypeError(f"Unsupported input type for predict: {type(X)}")

        results = []
        for val in values:
            diff = val - self.baseline_median
            if self.scaled_mad > 1e-8:
                z = diff / self.scaled_mad
            else:
                z = 0.0 if abs(diff) <= 1e-8 else (1.0 if diff > 0 else -1.0) * max(self.z_threshold + 0.5, abs(diff))

            is_anomaly = abs(z) >= self.z_threshold
            results.append({
                "current_value": val,
                "baseline_median": self.baseline_median,
                "baseline_mad": self.baseline_mad,
                "z_score": round(float(z), 4),
                "is_anomaly": is_anomaly,
            })

        return results


def train_anomaly_pipeline(
    history: Sequence[float],
    z_threshold: float = DEFAULT_Z_THRESHOLD,
    save_path: Optional[Union[str, Path]] = None,
) -> Tuple[RobustZScoreAnomalyDetector, Dict[str, Any]]:
    """
    Convenience pipeline entry point: fit detector -> optionally save.
    """
    detector = RobustZScoreAnomalyDetector(z_threshold=z_threshold)
    detector.fit(history)
    if save_path is not None:
        detector.save(save_path)
    return detector, {
        "sample_size": len(history),
        "method": "robust_zscore_mad",
        "baseline_median": detector.baseline_median,
        "baseline_mad": detector.baseline_mad,
        "model_version": detector.model_version,
    }


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.train", "status": "placeholder"}
