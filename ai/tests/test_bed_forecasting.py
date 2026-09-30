"""Tests for bed occupancy forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai.bed_forecasting.data import (
    chronological_train_test_split,
    resample_daily_bed_data,
    validate_and_load_series,
)
from ai.bed_forecasting.evaluate import evaluate_bed_forecast
from ai.bed_forecasting.features import generate_feature_matrix
from ai.bed_forecasting.predict import BedForecastingPredictor
from ai.bed_forecasting.schema import (
    BedForecastRequest,
    BedOccupancyRecord,
)
from ai.bed_forecasting.train import train_bed_forecaster


FACILITY_ID = "550e8400-e29b-41d4-a716-446655440000"


def _make_records(days: int = 60) -> list[dict]:
    """Create deterministic synthetic bed occupancy records."""

    dates = pd.date_range(
        "2026-07-01",
        periods=days,
        freq="D",
        tz="UTC",
    )

    rng = np.random.default_rng(42)

    capacities = {
        "icu": 20,
        "ventilator": 10,
        "general_ward": 100,
    }

    records: list[dict] = []

    for index, timestamp in enumerate(dates):
        for bed_type, capacity in capacities.items():
            occupancy = (
                0.55
                + 0.12 * np.sin(index / 7)
                + rng.normal(0, 0.03)
            )

            occupied = int(
                np.clip(
                    round(capacity * occupancy),
                    0,
                    capacity,
                )
            )

            records.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "bed_type": bed_type,
                    "total_beds": capacity,
                    "occupied_beds": occupied,
                    "admissions": float(
                        rng.poisson(
                            5
                            if bed_type == "general_ward"
                            else 2
                        )
                    ),
                    "discharges": float(
                        rng.poisson(
                            4
                            if bed_type == "general_ward"
                            else 2
                        )
                    ),
                    "emergency_cases": float(
                        rng.poisson(2)
                    ),
                    "disease_trend": float(
                        0.5 + 0.1 * np.sin(index / 10)
                    ),
                }
            )

    return records


@pytest.fixture
def raw_frame() -> pd.DataFrame:
    """Return validated raw bed data."""

    return validate_and_load_series(
        _make_records()
    )


@pytest.fixture
def daily_frame(
    raw_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return daily resampled bed data."""

    return resample_daily_bed_data(
        raw_frame
    )


@pytest.fixture
def training_result(daily_frame: pd.DataFrame):
    """Train a bed forecasting model."""

    return train_bed_forecaster(
        daily_frame
    )


def test_schema_accepts_valid_record() -> None:
    """Valid bed occupancy records should pass validation."""

    record = BedOccupancyRecord(
        timestamp="2026-07-01T00:00:00Z",
        bed_type="icu",
        total_beds=20,
        occupied_beds=15,
        admissions=2,
        discharges=1,
        emergency_cases=1,
        disease_trend=0.5,
    )

    assert record.bed_type == "icu"
    assert record.occupied_beds == 15


def test_schema_rejects_occupied_beds_above_capacity() -> None:
    """Occupied beds must not exceed total capacity."""

    with pytest.raises(ValueError):
        BedOccupancyRecord(
            timestamp="2026-07-01T00:00:00Z",
            bed_type="icu",
            total_beds=20,
            occupied_beds=21,
            admissions=2,
            discharges=1,
            emergency_cases=1,
            disease_trend=0.5,
        )


def test_data_validation_creates_occupancy(
    raw_frame: pd.DataFrame,
) -> None:
    """Validated data should contain occupancy between zero and one."""

    assert "occupancy" in raw_frame.columns

    assert raw_frame["occupancy"].between(
        0.0,
        1.0,
    ).all()


def test_daily_resampling_preserves_bed_types(
    daily_frame: pd.DataFrame,
) -> None:
    """Daily data should contain all supported bed types."""

    assert set(
        daily_frame["bed_type"].unique()
    ) == {
        "icu",
        "ventilator",
        "general_ward",
    }


def test_chronological_split_preserves_time_order(
    daily_frame: pd.DataFrame,
) -> None:
    """Training data must occur before validation data."""

    icu_data = daily_frame[
        daily_frame["bed_type"] == "icu"
    ].copy()

    train, test = chronological_train_test_split(
        icu_data,
        test_fraction=0.2,
    )

    assert train["date"].max() < test["date"].min()
    assert len(train) > 0
    assert len(test) > 0


def test_feature_generation_creates_lag_features(
    daily_frame: pd.DataFrame,
) -> None:
    """Feature generation should create lag and rolling features."""

    features, target = generate_feature_matrix(
        daily_frame,
        lags=(1, 2, 7),
        rolling_windows=(2, 7),
    )

    assert len(features) == len(target)

    assert "occupancy_lag_1" in features.columns
    assert "occupancy_lag_7" in features.columns

    assert (
        "occupancy_roll_mean_7"
        in features.columns
    )

    assert len(features) > 0


def test_training_produces_model(
    training_result,
) -> None:
    """Training should produce a usable XGBoost model."""

    assert training_result.model is not None

    assert (
        len(training_result.feature_columns)
        > 0
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
        training_result.residual_std
        >= 0.0
    )

    assert (
        0.05
        <= training_result.confidence
        <= 0.99
    )


def test_evaluation_returns_expected_metrics() -> None:
    """Evaluation should calculate forecast metrics."""

    actual = np.array(
        [
            0.50,
            0.60,
            0.70,
            0.80,
        ],
        dtype=float,
    )

    predicted = np.array(
        [
            0.52,
            0.58,
            0.68,
            0.78,
        ],
        dtype=float,
    )

    metrics = evaluate_bed_forecast(
        actual,
        predicted,
    )

    assert set(metrics) == {
        "mae",
        "rmse",
        "mape",
        "wape",
    }

    assert metrics["mae"] > 0.0
    assert metrics["rmse"] > 0.0


def test_prediction_returns_expected_horizons(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Prediction should return 24h, 48h and 7-day forecasts."""

    records = raw_frame[
        [
            "timestamp",
            "bed_type",
            "total_beds",
            "occupied_beds",
            "admissions",
            "discharges",
            "emergency_cases",
            "disease_trend",
        ]
    ].copy()

    records["timestamp"] = (
        records["timestamp"].astype(str)
    )

    request = BedForecastRequest(
        facility_id=FACILITY_ID,
        history=records.to_dict(
            orient="records"
        ),
        horizon_days=7,
    )

    response = BedForecastingPredictor(
        training_result
    ).predict(request)

    assert response.success is True

    assert (
        response.model_version
        == "bed-forecast-xgb-v1"
    )

    # 3 bed types × 3 forecast horizons.
    assert len(response.predictions) == 9

    assert {
        prediction.bed_type
        for prediction in response.predictions
    } == {
        "icu",
        "ventilator",
        "general_ward",
    }


def test_prediction_values_are_within_valid_ranges(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Predicted occupancy must remain within valid bounds."""

    records = raw_frame[
        [
            "timestamp",
            "bed_type",
            "total_beds",
            "occupied_beds",
            "admissions",
            "discharges",
            "emergency_cases",
            "disease_trend",
        ]
    ].copy()

    records["timestamp"] = (
        records["timestamp"].astype(str)
    )

    request = BedForecastRequest(
        facility_id=FACILITY_ID,
        history=records.to_dict(
            orient="records"
        ),
        horizon_days=7,
    )

    response = BedForecastingPredictor(
        training_result
    ).predict(request)

    for prediction in response.predictions:
        assert (
            0.0
            <= prediction.predicted_occupancy
            <= 1.0
        )

        assert (
            prediction.predicted_occupied_beds
            >= 0.0
        )

        assert (
            prediction.predicted_occupied_beds
            <= prediction.total_beds
        )