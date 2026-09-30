"""
Sanjeevani Grid - Anomaly Detection Data Layer
ai/anomaly_detection/data.py

Responsible for input validation, ingestion, and normalization of anomaly detection records.
"""

from typing import Any, Dict, Iterable, List

import pandas as pd

from ai.anomaly_detection.schema import AnomalyDetectionRequest


def validate_and_load_anomaly_records(
    records: Iterable[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Validate raw anomaly records and return a normalized pandas DataFrame.

    Parameters
    ----------
    records : Iterable[Dict[str, Any]]
        Raw dictionary records matching AnomalyDetectionRequest schema.

    Returns
    -------
    pd.DataFrame
        DataFrame of validated anomaly records.

    Raises
    ------
    ValueError
        If the records iterable is empty.
    pydantic.ValidationError
        If schema validation fails on any record.
    """
    rows: List[Dict[str, Any]] = []
    for record in records:
        req = AnomalyDetectionRequest.model_validate(record)
        rows.append(req.model_dump())

    if not rows:
        raise ValueError("Anomaly records dataset cannot be empty.")

    return pd.DataFrame(rows)


def placeholder() -> Dict[str, Any]:
    """Preserve backwards compatibility with early scaffold tests."""
    return {"module": "anomaly_detection.data", "status": "placeholder"}
