"""
Tests for the Sanjeevani Grid patient forecasting module.
"""

import numpy as np
import pandas as pd
import pytest

from ai.patient_forecasting.data import (
    chronological_train_test_split,
    resample_daily_visits,
    validate_and_load_series,
)
from ai.patient_forecasting.evaluate import evaluate_forecast
from ai.patient_forecasting.features import (
    build_lag_features,
    build_rolling_features,
    extract_calendar_features,
    generate_feature_matrix,
)
from ai.patient_forecasting.predict import (
    PatientForecastingPredictor,
)
from ai.patient_forecasting.schema import (
    PatientForecastRequest,
)
from ai.patient_forecasting.train import (
    train_patient_pipeline,
)


def make_records(count: int = 60) -> list[dict]:
    """Create deterministic synthetic patient-visit records for tests."""

    dates = pd.date_range(
        "2026-01-01",
        periods=count,
        freq="D",
        tz="UTC",
    )

    return [
        {
            "timestamp": (
                date.isoformat()
                .replace("+00:00", "Z")
            ),
            "visits": float(
                80
                + (index % 7) * 5
                + index * 0.3
            ),
        }
        for index, date in enumerate(dates)
    ]


def test_validate_and_load_series():
    """Patient visit records should be validated and sorted."""

    records = make_records(10)

    shuffled = [
        records[5],
        records[2],
        records[8],
        records[0],
    ]

    df = validate_and_load_series(shuffled)

    assert len(df) == 4
    assert "datetime" in df.columns
    assert "visits" in df.columns
    assert df["datetime"].is_monotonic_increasing


def test_negative_visits_are_rejected():
    """Negative patient visit counts should fail validation."""

    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "visits": -1,
        }
    ]

    with pytest.raises(ValueError):
        validate_and_load_series(records)


def test_resample_daily_visits():
    """Patient visits should be aggregated to daily totals."""

    records = [
        {
            "timestamp": "2026-01-01T08:00:00Z",
            "visits": 10,
        },
        {
            "timestamp": "2026-01-01T14:00:00Z",
            "visits": 15,
        },
        {
            "timestamp": "2026-01-02T09:00:00Z",
            "visits": 20,
        },
    ]

    df = validate_and_load_series(records)
    daily = resample_daily_visits(df)

    assert len(daily) == 2
    assert daily.loc[0, "visits"] == 25
    assert daily.loc[1, "visits"] == 20


def test_chronological_split():
    """Training data must occur before validation data."""

    records = make_records(20)
    df = validate_and_load_series(records)

    train_df, test_df = chronological_train_test_split(
        df,
        test_size=5,
    )

    assert len(train_df) == 15
    assert len(test_df) == 5
    assert (
        train_df["datetime"].max()
        < test_df["datetime"].min()
    )


def test_calendar_features():
    """Calendar features should be generated deterministically."""

    records = make_records(10)
    df = validate_and_load_series(records)

    result = extract_calendar_features(df)

    expected_columns = {
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend",
        "day_of_year",
        "dow_sin",
        "dow_cos",
        "month_sin",
        "month_cos",
    }

    assert expected_columns.issubset(
        result.columns
    )


def test_lag_features_do_not_use_future_values():
    """Lag features must use only previous observations."""

    records = make_records(20)
    df = validate_and_load_series(records)

    result = build_lag_features(
        df,
        target_col="visits",
        lags=[1, 7],
    )

    assert np.isnan(
        result.loc[0, "lag_1"]
    )

    assert result.loc[7, "lag_7"] == pytest.approx(
        result.loc[0, "visits"]
    )


def test_rolling_features_are_shifted():
    """Rolling features must exclude the current target."""

    records = make_records(20)
    df = validate_and_load_series(records)

    result = build_rolling_features(
        df,
        target_col="visits",
        windows=[7],
    )

    assert np.isnan(
        result.loc[0, "rolling_mean_7"]
    )

    expected = df.loc[:6, "visits"].mean()

    assert result.loc[7, "rolling_mean_7"] == pytest.approx(
        expected
    )


def test_feature_matrix():
    """Complete feature matrix should contain usable features."""

    records = make_records(30)
    df = validate_and_load_series(records)

    result, feature_columns = generate_feature_matrix(
        df,
        target_col="visits",
    )

    assert len(result) > 0
    assert len(feature_columns) > 0
    assert all(
        column in result.columns
        for column in feature_columns
    )
    assert not result[feature_columns].isna().any().any()


def test_forecasting_metrics():
    """Forecast evaluation should return the required metrics."""

    y_true = np.array(
        [100.0, 110.0, 120.0]
    )

    y_pred = np.array(
        [98.0, 112.0, 118.0]
    )

    metrics = evaluate_forecast(
        y_true,
        y_pred,
    )

    assert {
        "mae",
        "rmse",
        "mape",
        "wape",
    }.issubset(metrics.keys())

    assert metrics["mae"] >= 0
    assert metrics["rmse"] >= 0


def test_training_pipeline():
    """Patient forecasting model should train successfully."""

    records = make_records(60)

    model, metrics = train_patient_pipeline(
        records,
        test_size=7,
    )

    assert model.is_fitted
    assert model.booster is not None

    assert {
        "mae",
        "rmse",
        "mape",
        "wape",
    }.issubset(metrics.keys())

    assert model.residual_std >= 0
    assert 0.05 <= model.confidence <= 0.99


def test_seven_day_prediction():
    """Patient forecaster should produce a seven-day forecast."""

    records = make_records(60)

    model, _ = train_patient_pipeline(
        records,
        test_size=7,
    )

    predictor = PatientForecastingPredictor(
        forecaster=model
    )

    request = PatientForecastRequest(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        history=records,
        horizon_days=7,
    )

    result = predictor.predict(request)

    assert result["horizon_days"] == 7
    assert len(result["predictions"]) == 7
    assert 0.05 <= result["confidence"] <= 0.99

    for prediction in result["predictions"]:
        assert prediction["predicted_visits"] >= 0
        assert prediction["date"].endswith("Z")