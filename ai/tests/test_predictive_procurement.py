"""Tests for predictive procurement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai.predictive_procurement import (
    PredictiveProcurementPredictor,
    predict_procurement,
)
from ai.predictive_procurement.data import (
    records_to_dataframe,
)
from ai.predictive_procurement.evaluate import (
    evaluate_model,
)
from ai.predictive_procurement.features import (
    create_features,
    estimate_daily_demand,
)
from ai.predictive_procurement.train import (
    train_model,
)


def make_history(
    days: int = 21,
    daily_consumption: float = 10.0,
) -> list[dict]:
    """Create deterministic test history."""

    start = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    return [
        {
            "timestamp": (
                start + timedelta(days=index)
            ).isoformat(),
            "quantity_consumed": (
                daily_consumption
            ),
        }
        for index in range(days)
    ]


def make_payload(
    *,
    current_stock: float = 100.0,
    expected_incoming: float = 0.0,
    reserved_stock: float = 0.0,
    horizon_days: int = 7,
) -> dict:
    """Create a standard procurement request."""

    return {
        "facility_id": (
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        "item_id": "medicine-001",
        "current_stock": current_stock,
        "expected_incoming": expected_incoming,
        "reserved_stock": reserved_stock,
        "unit_cost": 5.0,
        "history": make_history(),
        "horizon_days": horizon_days,
    }


def test_records_to_dataframe():
    frame = records_to_dataframe(
        [
            {
                "timestamp": (
                    "2026-01-01T00:00:00+00:00"
                ),
                "quantity_consumed": 10,
            }
        ]
    )

    assert len(frame) == 1
    assert frame.iloc[0]["quantity_consumed"] == 10


def test_create_features():
    frame = records_to_dataframe(
        make_history()
    )

    features = create_features(
        frame,
        lookback_days=7,
    )

    assert "lag_1" in features.columns
    assert "lag_7" in features.columns
    assert "rolling_mean" in features.columns
    assert "month" in features.columns


def test_estimate_daily_demand():
    frame = records_to_dataframe(
        make_history(
            daily_consumption=10.0
        )
    )

    demand = estimate_daily_demand(
        frame,
        lookback_days=14,
    )

    assert demand >= 0
    assert demand == pytest.approx(
        10.0,
        abs=0.1,
    )


def test_train_model():
    frame = records_to_dataframe(
        make_history()
    )

    model = train_model(frame)

    assert model.model_version == (
        "predictive-procurement-v1"
    )
    assert model.average_daily_demand > 0


def test_evaluate_model():
    frame = records_to_dataframe(
        make_history()
    )

    metrics = evaluate_model(
        frame
    )

    assert set(metrics) == {
        "mae",
        "rmse",
        "mape",
        "wape",
    }

    for value in metrics.values():
        assert value >= 0


def test_predictor_returns_success():
    predictor = PredictiveProcurementPredictor()

    result = predictor.predict(
        make_payload()
    )

    assert result["success"] is True
    assert result["item_id"] == "medicine-001"


def test_expected_demand():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=100,
        history=make_history(),
        horizon_days=7,
    )

    assert result["expected_demand"] == pytest.approx(
        70.0,
        abs=2.0,
    )


def test_procurement_required_when_stock_is_low():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=10,
        history=make_history(),
        horizon_days=7,
    )

    assert (
        result["suggested_procurement_quantity"]
        > 0
    )


def test_no_procurement_when_stock_is_sufficient():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=200,
        history=make_history(),
        horizon_days=7,
    )

    assert (
        result["suggested_procurement_quantity"]
        == pytest.approx(0.0)
    )


def test_incoming_stock_reduces_procurement():
    without_incoming = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=20,
        history=make_history(),
        horizon_days=7,
    )

    with_incoming = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=20,
        expected_incoming=50,
        history=make_history(),
        horizon_days=7,
    )

    assert (
        with_incoming[
            "suggested_procurement_quantity"
        ]
        <= without_incoming[
            "suggested_procurement_quantity"
        ]
    )


def test_reserved_stock_is_excluded():
    result_without_reserved = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=100,
        history=make_history(),
        horizon_days=7,
    )

    result_with_reserved = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=100,
        reserved_stock=50,
        history=make_history(),
        horizon_days=7,
    )

    assert (
        result_with_reserved[
            "suggested_procurement_quantity"
        ]
        >= result_without_reserved[
            "suggested_procurement_quantity"
        ]
    )


def test_shortage_date_is_detected():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=15,
        history=make_history(),
        horizon_days=7,
    )

    assert (
        result["expected_shortage_date"]
        is not None
    )


def test_forecast_length():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=100,
        history=make_history(),
        horizon_days=7,
    )

    assert len(result["forecast"]) == 7


def test_forecast_has_required_fields():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=100,
        history=make_history(),
        horizon_days=3,
    )

    point = result["forecast"][0]

    assert "date" in point
    assert "predicted_demand" in point
    assert "cumulative_demand" in point
    assert "projected_stock" in point
    assert "shortage" in point


def test_procurement_cost():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=10,
        unit_cost=5.0,
        history=make_history(),
        horizon_days=7,
    )

    assert result[
        "estimated_procurement_cost"
    ] == pytest.approx(
        result[
            "suggested_procurement_quantity"
        ] * 5.0
    )


def test_explanation_present():
    result = predict_procurement(
        facility_id=(
            "550e8400-e29b-41d4-a716-446655440000"
        ),
        item_id="medicine-001",
        current_stock=100,
        history=make_history(),
    )

    assert len(result["explanation"]) >= 3


def test_empty_history_rejected():
    with pytest.raises(ValueError):
        predict_procurement(
            facility_id=(
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            item_id="medicine-001",
            current_stock=100,
            history=[],
        )


def test_insufficient_history_rejected():
    with pytest.raises(ValueError):
        predict_procurement(
            facility_id=(
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            item_id="medicine-001",
            current_stock=100,
            history=make_history(days=3),
        )


def test_negative_stock_rejected():
    with pytest.raises(ValueError):
        predict_procurement(
            facility_id=(
                "550e8400-e29b-41d4-a716-446655440000"
            ),
            item_id="medicine-001",
            current_stock=-1,
            history=make_history(),
        )