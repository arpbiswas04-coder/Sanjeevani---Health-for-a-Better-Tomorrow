"""
Sanjeevani Grid - Artifact Serialization & Deserialization
ai/common/serialization.py

Provides joblib-based serialization for trained model artifacts, feature encoders,
and evaluation reports. Ensures parent directories exist and includes graceful
fallback when joblib is pending environment installation.
"""

from pathlib import Path
from typing import Any, Union

try:
    import joblib
    _HAS_JOBLIB = True
except ImportError:
    import pickle
    _HAS_JOBLIB = False


def save_artifact(obj: Any, filepath: Union[str, Path]) -> Path:
    """
    Serialize an object/model artifact to disk.
    Creates any required parent directories automatically.

    Uses joblib when available; falls back to standard pickle if joblib
    is pending environment installation.
    """
    path = Path(filepath).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if _HAS_JOBLIB:
        joblib.dump(obj, path)
    else:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

    return path


def load_artifact(filepath: Union[str, Path]) -> Any:
    """
    Deserialize a model artifact or object from disk.
    Raises FileNotFoundError if the target artifact file does not exist.
    """
    path = Path(filepath).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Model artifact not found at: {path}")

    if _HAS_JOBLIB:
        return joblib.load(path)
    else:
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)
