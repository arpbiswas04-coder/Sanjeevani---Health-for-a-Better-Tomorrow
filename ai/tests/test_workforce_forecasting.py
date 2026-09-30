"""Tests for workforce forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai.workforce_forecasting.data import (
    resample_daily_workforce_data,
    validate_and_load_series,
)
from ai.workforce_forecasting.evaluate import (
    evaluate_workforce_forecast,
)
from ai.workforce_forecasting.features import (
    generate_feature_matrix,
)
from ai.workforce_forecasting.predict import (
    WorkforceForecastingPredictor,
)
from ai.workforce_forecasting.schema import (
    WorkforceForecastRequest,
    WorkforceRecord,
)
from ai.workforce_forecasting.train import (
    train_workforce_forecaster,
)


FACILITY_ID = "550e8400-e29b-41d4-a716-446655440000"


def _make_records(
    days: int = 30,
) -> list[dict]:
    """Create deterministic synthetic workforce data."""

    dates = pd.date_range(
        "2026-07-01",
        periods=days,
        freq="D",
        tz="UTC",
    )

    rng = np.random.default_rng(42)

    departments = {
        "icu": 20,
        "general_ward": 80,
        "emergency": 40,
    }

    staff_ratios = {
        "doctor": 10.0,
        "nurse": 4.0,
        "support": 8.0,
    }

    records: list[dict] = []

    for index, timestamp in enumerate(dates):
        for department, capacity in departments.items():
            occupancy = float(
                np.clip(
                    0.55
                    + 0.08 * np.sin(index / 6)
                    + rng.normal(0, 0.02),
                    0.0,
                    1.0,
                )
            )

            patient_count = (
                capacity * occupancy
            )

            for staff_role, ratio in (
                staff_ratios.items()
            ):
                scheduled_staff = int(
                    np.ceil(
                        patient_count / ratio
                    )
                )

                records.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "department": department,
                        "patient_count": float(
                            patient_count
                        ),
                        "occupancy": occupancy,
                        "scheduled_staff": scheduled_staff,
                        "staff_role": staff_role,
                    }
                )

    return records


@pytest.fixture
def raw_frame() -> pd.DataFrame:
    """Return validated workforce data."""

    return validate_and_load_series(
        _make_records()
    )


@pytest.fixture
def daily_frame(
    raw_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return daily workforce data."""

    return resample_daily_workforce_data(
        raw_frame
    )


@pytest.fixture
def training_result(
    daily_frame: pd.DataFrame,
):
    """Train a workforce forecasting model."""

    return train_workforce_forecaster(
        daily_frame
    )


def test_schema_accepts_valid_record() -> None:
    """Valid workforce records should pass validation."""

    record = WorkforceRecord(
        timestamp="2026-07-01T00:00:00Z",
        department="icu",
        patient_count=15.0,
        occupancy=0.75,
        scheduled_staff=4,
        staff_role="nurse",
    )

    assert record.department == "icu"
    assert record.staff_role == "nurse"
    assert record.patient_count == 15.0


def test_schema_rejects_invalid_occupancy() -> None:
    """Occupancy must remain between zero and one."""

    with pytest.raises(ValueError):
        WorkforceRecord(
            timestamp="2026-07-01T00:00:00Z",
            department="icu",
            patient_count=15.0,
            occupancy=1.5,
            scheduled_staff=4,
            staff_role="nurse",
        )


def test_data_validation(
    raw_frame: pd.DataFrame,
) -> None:
    """Validated data should contain required columns."""

    required = {
        "timestamp",
        "department",
        "patient_count",
        "occupancy",
        "scheduled_staff",
        "staff_role",
        "date",
    }

    assert required.issubset(
        raw_frame.columns
    )

    assert raw_frame["patient_count"].ge(
        0.0
    ).all()

    assert raw_frame["scheduled_staff"].ge(
        0
    ).all()


def test_daily_resampling(
    daily_frame: pd.DataFrame,
) -> None:
    """Daily aggregation should preserve departments and roles."""

    assert set(
        daily_frame["department"].unique()
    ) == {
        "icu",
        "general_ward",
        "emergency",
    }

    assert set(
        daily_frame["staff_role"].unique()
    ) == {
        "doctor",
        "nurse",
        "support",
    }


def test_feature_generation(
    daily_frame: pd.DataFrame,
) -> None:
    """Feature generation should create lag and rolling features."""

    features, target = (
        generate_feature_matrix(
            daily_frame,
            lags=(1, 7),
            rolling_windows=(3, 7),
        )
    )

    assert len(features) == len(target)
    assert len(features) > 0

    assert (
        "patient_count_lag_1"
        in features.columns
    )

    assert (
        "patient_count_lag_7"
        in features.columns
    )

    assert (
        "patient_count_roll_mean_7"
        in features.columns
    )


def test_training_produces_model(
    training_result,
) -> None:
    """Training should produce a usable model."""

    assert training_result.model is not None

    assert (
        len(
            training_result.feature_columns
        )
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


def test_evaluation_metrics() -> None:
    """Evaluation should return all required metrics."""

    actual = np.array(
        [
            10.0,
            20.0,
            30.0,
            40.0,
        ]
    )

    predicted = np.array(
        [
            11.0,
            19.0,
            31.0,
            38.0,
        ]
    )

    metrics = evaluate_workforce_forecast(
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


def test_prediction_returns_workforce_requirements(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Prediction should return staff requirements."""

    records = raw_frame[
        [
            "timestamp",
            "department",
            "patient_count",
            "occupancy",
            "scheduled_staff",
            "staff_role",
        ]
    ].copy()

    records["timestamp"] = (
        records["timestamp"].astype(str)
    )

    request = WorkforceForecastRequest(
        facility_id=FACILITY_ID,
        history=records.to_dict(
            orient="records"
        ),
        horizon_days=7,
    )

    response = (
        WorkforceForecastingPredictor(
            training_result
        ).predict(request)
    )

    assert response.success is True

    assert (
        response.model_version
        == "workforce-forecast-xgb-v1"
    )

    assert len(
        response.predictions
    ) > 0

    for prediction in response.predictions:
        assert (
            prediction.predicted_patients
            >= 0.0
        )

        assert (
            prediction.required_staff
            >= 0
        )

        assert (
            prediction.scheduled_staff
            >= 0
        )


def test_staffing_gap_is_correct(
    raw_frame: pd.DataFrame,
    training_result,
) -> None:
    """Staffing gap should equal required minus scheduled."""

    records = raw_frame[
        [
            "timestamp",
            "department",
            "patient_count",
            "occupancy",
            "scheduled_staff",
            "staff_role",
        ]
    ].copy()

    records["timestamp"] = (
        records["timestamp"].astype(str)
    )

    request = WorkforceForecastRequest(
        facility_id=FACILITY_ID,
        history=records.to_dict(
            orient="records"
        ),
        horizon_days=1,
    )

    response = (
        WorkforceForecastingPredictor(
            training_result
        ).predict(request)
    )

    assert len(
        response.predictions
    ) > 0

    for prediction in response.predictions:
        assert (
            prediction.staffing_gap
            == (
                prediction.required_staff
                - prediction.scheduled_staff
            )
        )

        assert (
            prediction.staffing_shortage
            == (
                prediction.staffing_gap > 0
            )
        )