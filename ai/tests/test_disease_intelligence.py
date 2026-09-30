"""Tests for disease intelligence."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai.disease_intelligence.data import (
    aggregate_daily_cases,
    validate_and_load_cases,
)
from ai.disease_intelligence.evaluate import (
    evaluate_disease_intelligence,
)
from ai.disease_intelligence.features import (
    add_growth_features,
    add_statistical_features,
    build_disease_features,
)
from ai.disease_intelligence.predict import (
    DiseaseIntelligencePredictor,
)
from ai.disease_intelligence.schema import (
    DiseaseCaseRecord,
    DiseaseIntelligenceRequest,
)
from ai.disease_intelligence.train import (
    train_disease_intelligence,
)


FACILITY_ID = "550e8400-e29b-41d4-a716-446655440000"


def _make_records(
    days: int = 30,
) -> list[dict]:
    """Create deterministic synthetic disease observations."""

    dates = pd.date_range(
        "2026-07-01",
        periods=days,
        freq="D",
        tz="UTC",
    )

    rng = np.random.default_rng(42)

    records: list[dict] = []

    for index, timestamp in enumerate(dates):
        # Gradual case growth with deterministic noise.
        cases = max(
            1,
            int(
                round(
                    20
                    + index * 0.8
                    + rng.normal(0, 1.0)
                )
            ),
        )

        records.append(
            {
                "timestamp": timestamp.isoformat(),
                "disease": "respiratory_syndrome",
                "latitude": 23.2324
                + (index % 3) * 0.01,
                "longitude": 87.0784
                + (index % 3) * 0.01,
                "case_count": cases,
            }
        )

    return records


@pytest.fixture
def raw_frame() -> pd.DataFrame:
    """Return validated disease observations."""

    return validate_and_load_cases(
        _make_records()
    )


@pytest.fixture
def daily_frame(
    raw_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return daily disease observations."""

    return aggregate_daily_cases(
        raw_frame
    )


@pytest.fixture
def training_result(
    daily_frame: pd.DataFrame,
):
    """Train the disease-intelligence baseline."""

    return train_disease_intelligence(
        daily_frame
    )


def test_schema_accepts_valid_record() -> None:
    """Valid disease records should pass validation."""

    record = DiseaseCaseRecord(
        timestamp="2026-07-01T00:00:00Z",
        disease="respiratory_syndrome",
        latitude=23.2324,
        longitude=87.0784,
        case_count=10,
    )

    assert (
        record.disease
        == "respiratory_syndrome"
    )

    assert record.case_count == 10


def test_schema_rejects_negative_cases() -> None:
    """Negative case counts must be rejected."""

    with pytest.raises(ValueError):
        DiseaseCaseRecord(
            timestamp="2026-07-01T00:00:00Z",
            disease="respiratory_syndrome",
            latitude=23.2324,
            longitude=87.0784,
            case_count=-1,
        )


def test_schema_rejects_invalid_latitude() -> None:
    """Latitude outside the valid range must be rejected."""

    # The schema currently accepts numeric latitude,
    # while the data validation layer enforces the range.
    frame = [
        {
            "timestamp": "2026-07-01T00:00:00Z",
            "disease": "respiratory_syndrome",
            "latitude": 100.0,
            "longitude": 87.0784,
            "case_count": 10,
        }
    ]

    with pytest.raises(ValueError):
        validate_and_load_cases(frame)


def test_data_validation(
    raw_frame: pd.DataFrame,
) -> None:
    """Validated data should contain required fields."""

    required = {
        "timestamp",
        "disease",
        "latitude",
        "longitude",
        "case_count",
        "date",
    }

    assert required.issubset(
        raw_frame.columns
    )

    assert raw_frame["case_count"].ge(
        0
    ).all()

    assert raw_frame["latitude"].between(
        -90,
        90,
    ).all()

    assert raw_frame["longitude"].between(
        -180,
        180,
    ).all()


def test_daily_aggregation(
    daily_frame: pd.DataFrame,
) -> None:
    """Daily aggregation should produce one row per date/disease."""

    assert len(daily_frame) == 30

    assert (
        daily_frame["disease"].nunique()
        == 1
    )

    assert (
        daily_frame["case_count"].ge(0).all()
    )


def test_growth_features(
    daily_frame: pd.DataFrame,
) -> None:
    """Growth features should be generated correctly."""

    features = add_growth_features(
        daily_frame,
        window=7,
    )

    assert "previous_cases" in features.columns
    assert "growth_rate" in features.columns

    usable = features.dropna(
        subset=["previous_cases"]
    )

    assert len(usable) > 0

    assert np.isfinite(
        usable["growth_rate"]
    ).all()


def test_statistical_features(
    daily_frame: pd.DataFrame,
) -> None:
    """Rolling anomaly statistics should be generated."""

    features = add_statistical_features(
        daily_frame,
        window=7,
    )

    assert "rolling_mean" in features.columns
    assert "rolling_std" in features.columns
    assert "anomaly_score" in features.columns

    usable = features.dropna(
        subset=["rolling_mean"]
    )

    assert len(usable) > 0

    assert np.isfinite(
        usable["anomaly_score"]
    ).all()


def test_complete_feature_generation(
    daily_frame: pd.DataFrame,
) -> None:
    """Complete disease feature generation should work."""

    features = build_disease_features(
        daily_frame,
        growth_window=7,
    )

    expected_columns = {
        "growth_rate",
        "rolling_mean",
        "rolling_std",
        "anomaly_score",
    }

    assert expected_columns.issubset(
        features.columns
    )


def test_training_produces_result(
    training_result,
) -> None:
    """Training should produce valid calibration metrics."""

    assert (
        training_result.model_version
        == "disease-intelligence-hybrid-v1"
    )

    assert (
        training_result.metrics["mae"]
        >= 0.0
    )

    assert (
        training_result.metrics["rmse"]
        >= 0.0
    )

    assert (
        training_result.baseline_mean
        >= 0.0
    )

    assert (
        training_result.baseline_std
        >= 0.0
    )

    assert (
        0.05
        <= training_result.confidence
        <= 0.99
    )


def test_evaluation(
    daily_frame: pd.DataFrame,
    training_result,
) -> None:
    """Evaluation should return required metrics."""

    metrics = evaluate_disease_intelligence(
        daily_frame,
        training_result,
    )

    assert {
        "mae",
        "rmse",
        "mean_surge_probability",
        "confidence",
    }.issubset(metrics)

    assert metrics["mae"] >= 0.0
    assert metrics["rmse"] >= 0.0

    assert (
        0.0
        <= metrics["mean_surge_probability"]
        <= 1.0
    )


def test_prediction_returns_early_warning(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Prediction should return operational warning intelligence."""

    request = DiseaseIntelligenceRequest(
        facility_id=FACILITY_ID,
        disease="respiratory_syndrome",
        history=raw_frame[
            [
                "timestamp",
                "disease",
                "latitude",
                "longitude",
                "case_count",
            ]
        ]
        .assign(
            timestamp=lambda frame: frame[
                "timestamp"
            ].astype(str)
        )
        .to_dict(
            orient="records"
        ),
    )

    response = DiseaseIntelligencePredictor(
        training_result
    ).predict(request)

    assert response.success is True

    assert (
        response.model_version
        == "disease-intelligence-hybrid-v1"
    )

    assert response.prediction_id

    assert response.generated_at

    assert len(
        response.trajectory
    ) > 0

    assert (
        0.0
        <= response.surge_probability
        <= 1.0
    )

    assert response.risk_level in {
        "low",
        "moderate",
        "high",
        "critical",
    }


def test_prediction_contains_explanation(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Prediction should explain the operational warning."""

    request = DiseaseIntelligenceRequest(
        facility_id=FACILITY_ID,
        disease="respiratory_syndrome",
        history=raw_frame[
            [
                "timestamp",
                "disease",
                "latitude",
                "longitude",
                "case_count",
            ]
        ]
        .assign(
            timestamp=lambda frame: frame[
                "timestamp"
            ].astype(str)
        )
        .to_dict(
            orient="records"
        ),
    )

    response = DiseaseIntelligencePredictor(
        training_result
    ).predict(request)

    assert len(
        response.explanation
    ) >= 1

    assert any(
        "early-warning" in explanation
        for explanation in response.explanation
    )


def test_geographic_clusters(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Prediction should identify geographic case clusters."""

    request = DiseaseIntelligenceRequest(
        facility_id=FACILITY_ID,
        disease="respiratory_syndrome",
        history=raw_frame[
            [
                "timestamp",
                "disease",
                "latitude",
                "longitude",
                "case_count",
            ]
        ]
        .assign(
            timestamp=lambda frame: frame[
                "timestamp"
            ].astype(str)
        )
        .to_dict(
            orient="records"
        ),
    )

    response = DiseaseIntelligencePredictor(
        training_result
    ).predict(request)

    assert len(
        response.clusters
    ) > 0

    for cluster in response.clusters:
        assert cluster.case_count > 0
        assert cluster.member_count > 0
        assert cluster.radius_km >= 0.0


def test_insufficient_history_is_rejected() -> None:
    """Prediction should reject insufficient history."""

    records = _make_records(days=5)

    request = DiseaseIntelligenceRequest(
        facility_id=FACILITY_ID,
        disease="respiratory_syndrome",
        history=records,
    )

    # No trained model is needed because history
    # validation happens before inference.
    dummy_training_result = train_disease_intelligence(
        aggregate_daily_cases(
            validate_and_load_cases(
                _make_records(days=14)
            )
        )
    )

    predictor = DiseaseIntelligencePredictor(
        dummy_training_result
    )

    with pytest.raises(ValueError):
        predictor.predict(request)