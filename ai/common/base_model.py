"""
Sanjeevani Grid - Common Base Model Abstractions
ai/common/base_model.py

Defines core abstract base classes for forecasting models, inference services,
and risk evaluators across the Member 3 AI subsystem.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.common.serialization import load_artifact, save_artifact


class BaseForecaster(ABC):
    """
    Abstract base class for all time-series and regression forecasters in Sanjeevani Grid.

    Subclasses must implement fit and predict methods.
    Provides standard serialization and persistence capabilities.
    """

    def __init__(self, model_name: str = "BaseForecaster") -> None:
        self.model_name = model_name
        self.is_fitted: bool = False

    @abstractmethod
    def fit(self, X: Any, y: Optional[Any] = None, **kwargs: Any) -> "BaseForecaster":
        """
        Fit model parameters to training data.

        Returns self for method chaining.
        """
        raise NotImplementedError

    @abstractmethod
    def predict(self, X: Any, **kwargs: Any) -> Any:
        """
        Generate predictions / forecasts from input features.
        """
        raise NotImplementedError

    def save(self, filepath: Union[str, Path]) -> Path:
        """Serialize fitted model artifact to disk."""
        return save_artifact(self, filepath)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "BaseForecaster":
        """
        Deserialize model artifact from disk and verify type safety.
        """
        model = load_artifact(filepath)
        if not isinstance(model, cls):
            raise TypeError(
                f"Loaded artifact of type {type(model).__name__} is not an instance of {cls.__name__}"
            )
        return model


class BasePredictor(ABC):
    """
    Abstract base class for inference service interfaces.
    Enforces schema validation on input payloads and returns typed prediction payloads.
    """

    @abstractmethod
    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input payload and execute model inference.
        """
        raise NotImplementedError


class BaseScorer(ABC):
    """
    Abstract base class for risk scoring and resilience index evaluators.
    """

    @abstractmethod
    def calculate_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute normalized scores and canonical risk levels from input indicators.
        """
        raise NotImplementedError
