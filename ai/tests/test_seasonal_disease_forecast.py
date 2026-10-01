"""Tests for seasonal disease forecasting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from ai.seasonal_disease_forecast.data import (
    chronological_split,
    records_to_dataframe,
    validate_history_length,
)
from ai.seasonal_disease_forecast.evaluate import (
    calculate_seasonal_signal,
)
from ai.seasonal_disease_forecast.features import (
    create_features,
    get_feature_columns,
)
from ai.seasonal_disease_forecast.predict import (
    SeasonalDiseaseForecastPredictor,
)
from ai.seasonal_disease_forecast.train import (
    train_model,
)


def make_history(
    days: int = 90,
    disease: str = "influenza",
) -> list[dict]:
    """Create deterministic synthetic history for tests."""

    start = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    records = []

    for index in range(days):
        timestamp = (
            start
            + timedelta(days=index)
        )

        seasonal_component = (
            10.0
            * np.sin(
                2.0
                * np.pi
                * index
                / 30.0
            )
        )

        weekly_component = (
            3.0
            * np.sin(
                2.0
                * np.pi
                * index
                / 7.0
            )
        )

        cases = max(
            1.0,
            50.0
            + seasonal_component
            + weekly_component,
        )

        records.append(
            {
                "timestamp": timestamp.isoformat(),
                "disease": disease,
                "case_count": float(cases),
            }
        )

    return records


def make_frame(
    days: int = 90,
) -> pd.DataFrame:
    """Create a deterministic disease time series."""

    history = make_history(days)

    from ai.seasonal_disease_forecast.schema import (
        SeasonalDiseaseRecord,
    )

    records = [
        SeasonalDiseaseRecord.model_validate(
            record
        )
        for record in history
    ]

    return records_to_dataframe(
        records,
        disease="influenza",
    )


# ---------------------------------------------------------------------------
# Module-scoped fixture: train once, reuse across all inference tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fitted_predictor() -> SeasonalDiseaseForecastPredictor:
    """Return a fully fitted predictor trained once for the module."""
    from ai.seasonal_disease_forecast.train import train_model as _train

    frame = make_frame(120)
    model_bundle = _train(frame)
    return SeasonalDiseaseForecastPredictor(model_bundle=model_bundle)


# ---------------------------------------------------------------------------
# Data / feature tests
# ---------------------------------------------------------------------------

def test_records_are_converted_to_daily_series() -> None:
    frame = make_frame(90)

    assert len(frame) == 90
    assert "case_count" in frame.columns
    assert frame.index.is_monotonic_increasing


def test_records_filter_by_disease() -> None:
    history = make_history(30)

    history.append(
        {
            "timestamp": (
                datetime(
                    2026,
                    2,
                    1,
                    tzinfo=timezone.utc,
                ).isoformat()
            ),
            "disease": "dengue",
            "case_count": 100.0,
        }
    )

    from ai.seasonal_disease_forecast.schema import (
        SeasonalDiseaseRecord,
    )

    records = [
        SeasonalDiseaseRecord.model_validate(
            record
        )
        for record in history
    ]

    frame = records_to_dataframe(
        records,
        disease="influenza",
    )

    assert len(frame) >= 30
    assert frame["case_count"].max() < 100.0


def test_history_length_validation() -> None:
    frame = make_frame(30)

    validate_history_length(
        frame,
        min_history_points=30,
    )


def test_history_length_rejects_short_series() -> None:
    frame = make_frame(10)

    with pytest.raises(ValueError):
        validate_history_length(
            frame,
            min_history_points=30,
        )


def test_chronological_split_preserves_order() -> None:
    frame = make_frame(90)

    train, validation = chronological_split(
        frame
    )

    assert len(train) > len(validation)
    assert train.index[-1] < validation.index[0]


def test_feature_engineering_creates_seasonal_features() -> None:
    frame = make_frame(90)

    features = create_features(
        frame,
        lags=(1, 7, 14),
        rolling_windows=(7, 14),
    )

    assert not features.empty

    expected_columns = {
        "month",
        "month_sin",
        "month_cos",
        "week_sin",
        "week_cos",
        "day_of_week_sin",
        "day_of_week_cos",
        "lag_1",
        "lag_7",
        "lag_14",
        "rolling_mean_7",
        "rolling_mean_14",
    }

    assert expected_columns.issubset(
        set(features.columns)
    )


def test_feature_columns_exclude_target() -> None:
    frame = make_frame(90)

    features = create_features(
        frame,
        lags=(1, 7),
        rolling_windows=(7,),
    )

    columns = get_feature_columns(
        features
    )

    assert "case_count" not in columns
    assert len(columns) > 0


def test_seasonal_signal_is_non_negative() -> None:
    frame = make_frame(90)

    signal = calculate_seasonal_signal(
        frame
    )

    assert signal >= 0.0


def test_model_training_returns_model() -> None:
    frame = make_frame(120)

    model_bundle = train_model(
        frame
    )

    assert model_bundle.model is not None
    assert model_bundle.feature_columns
    assert model_bundle.residual_std >= 0.0

    assert "mae" in model_bundle.metrics
    assert "rmse" in model_bundle.metrics
    assert "mape" in model_bundle.metrics
    assert "wape" in model_bundle.metrics


# ---------------------------------------------------------------------------
# Lifecycle regression tests
# ---------------------------------------------------------------------------

def test_predictor_without_fitted_model_raises_runtime_error() -> None:
    """An unfitted predictor must raise RuntimeError — not retrain silently."""
    predictor = SeasonalDiseaseForecastPredictor()

    assert predictor.is_fitted is False

    with pytest.raises(RuntimeError, match="no fitted model"):
        predictor.predict(
            {
                "facility_id": (
                    "550e8400-e29b-41d4-a716-446655440000"
                ),
                "disease": "influenza",
                "history": make_history(120),
                "horizon_days": 7,
            }
        )


def test_predict_does_not_retrain_model(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    """predict() must never replace the model_bundle that was supplied."""
    bundle_before = fitted_predictor.model_bundle

    fitted_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )

    assert fitted_predictor.model_bundle is bundle_before


def test_predictor_lifecycle_fit_and_artifact_load(
    tmp_path: object,
) -> None:
    """Full lifecycle: unfitted->fit->predict, then save->load via artifact_path."""
    frame = make_frame(120)

    predictor = SeasonalDiseaseForecastPredictor()
    assert predictor.is_fitted is False

    predictor.fit(frame)
    assert predictor.is_fitted is True
    assert predictor.model_bundle is not None

    result = predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )
    assert result["success"] is True

    # Save model_bundle and reload via artifact_path
    artifact_file = tmp_path / "test_bundle.joblib"  # type: ignore[operator]
    from ai.common.serialization import save_artifact
    save_artifact(predictor.model_bundle, artifact_file)

    loaded_predictor = SeasonalDiseaseForecastPredictor(
        artifact_path=artifact_file
    )
    assert loaded_predictor.is_fitted is True

    loaded_result = loaded_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )
    assert loaded_result["success"] is True


def test_predictor_initialized_with_model_bundle_is_fitted() -> None:
    """Supplying model_bundle at construction time marks predictor as fitted."""
    frame = make_frame(120)
    bundle = train_model(frame)

    predictor = SeasonalDiseaseForecastPredictor(model_bundle=bundle)
    assert predictor.is_fitted is True
    assert predictor.model_bundle is bundle


# ---------------------------------------------------------------------------
# Inference tests (use fitted_predictor fixture to avoid repeated training)
# ---------------------------------------------------------------------------

def test_predictor_generates_requested_horizon(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    result = fitted_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )

    assert result["success"] is True
    assert result["disease"] == "influenza"
    assert result["horizon_days"] == 7
    assert len(result["predictions"]) == 7


def test_predictions_are_non_negative(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    result = fitted_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )

    for prediction in result["predictions"]:
        assert prediction["predicted_cases"] >= 0.0
        assert prediction["lower_bound"] >= 0.0
        assert prediction["upper_bound"] >= 0.0
        assert (
            prediction["lower_bound"]
            <= prediction["predicted_cases"]
            <= prediction["upper_bound"]
        )


def test_prediction_confidence_is_bounded(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    result = fitted_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )

    for prediction in result["predictions"]:
        assert 0.0 <= prediction["confidence"] <= 1.0


def test_short_history_is_rejected(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    with pytest.raises(ValueError):
        fitted_predictor.predict(
            {
                "facility_id": (
                    "550e8400-e29b-41d4-a716-446655440000"
                ),
                "disease": "influenza",
                "history": make_history(10),
                "horizon_days": 7,
            }
        )


def test_wrong_disease_is_rejected(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    with pytest.raises(ValueError):
        fitted_predictor.predict(
            {
                "facility_id": (
                    "550e8400-e29b-41d4-a716-446655440000"
                ),
                "disease": "dengue",
                "history": make_history(120),
                "horizon_days": 7,
            }
        )


def test_model_version_is_present(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    result = fitted_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )

    assert result["model_version"] == (
        "seasonal-disease-forecast-v1"
    )


def test_explanation_contains_forecasting_context(
    fitted_predictor: SeasonalDiseaseForecastPredictor,
) -> None:
    result = fitted_predictor.predict(
        {
            "facility_id": (
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            "disease": "influenza",
            "history": make_history(120),
            "horizon_days": 7,
        }
    )

    explanation = " ".join(
        result["explanation"]
    ).lower()

    assert "forecast" in explanation
    assert "diagnostic" in explanation