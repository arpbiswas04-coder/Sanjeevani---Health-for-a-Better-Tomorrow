"""Tests for inventory simulation."""

from __future__ import annotations

import pytest

from ai.inventory_simulation import (
    InventorySimulationPredictor,
    simulate_inventory,
)
from ai.inventory_simulation.data import (
    normalize_incoming,
    validate_demand,
)
from ai.inventory_simulation.evaluate import (
    evaluate_projection,
)
from ai.inventory_simulation.features import (
    calculate_daily_inventory,
    calculate_projected_ending_stock,
)
from ai.inventory_simulation.train import (
    train_model,
)


FACILITY_ID = (
    "550e8400-e29b-41d4-a716-446655440000"
)


def make_payload(
    *,
    current_stock: float = 100.0,
    demand: list[float] | None = None,
    incoming: list[float] | None = None,
    reserved_stock: float = 0.0,
    safety_stock: float = 20.0,
) -> dict:
    """Create a deterministic simulation payload."""

    return {
        "facility_id": FACILITY_ID,
        "item_id": "medicine-001",
        "current_stock": current_stock,
        "reserved_stock": reserved_stock,
        "predicted_demand": (
            demand or [10.0] * 7
        ),
        "expected_incoming": (
            incoming or []
        ),
        "start_date": (
            "2026-01-01T00:00:00+00:00"
        ),
        "safety_stock": safety_stock,
    }


def test_validate_demand():
    result = validate_demand(
        [10, 20, 30]
    )

    assert result == [
        10.0,
        20.0,
        30.0,
    ]


def test_validate_empty_demand():
    with pytest.raises(ValueError):
        validate_demand([])


def test_validate_negative_demand():
    with pytest.raises(ValueError):
        validate_demand(
            [10, -1, 20]
        )


def test_normalize_incoming():
    result = normalize_incoming(
        [10, 20],
        4,
    )

    assert result == [
        10.0,
        20.0,
        0.0,
        0.0,
    ]


def test_daily_inventory_formula():
    state = calculate_daily_inventory(
        opening_stock=100,
        expected_incoming=20,
        predicted_demand=30,
        reserved_stock=10,
    )

    assert state.closing_stock == 80


def test_projected_ending_stock():
    result = calculate_projected_ending_stock(
        current_stock=100,
        expected_incoming=50,
        predicted_demand=80,
        reserved_stock=10,
    )

    assert result == 60


def test_train_model():
    model = train_model()

    assert model.model_version == (
        "inventory-simulation-v1"
    )


def test_basic_simulation():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10, 10, 10],
    )

    assert result["success"] is True
    assert result["projected_ending_stock"] == 70


def test_trajectory_length():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10] * 7,
    )

    assert len(result["trajectory"]) == 7


def test_incoming_stock_increases_ending_stock():
    without_incoming = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10] * 7,
    )

    with_incoming = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10] * 7,
        expected_incoming=[50],
    )

    assert (
        with_incoming[
            "projected_ending_stock"
        ]
        > without_incoming[
            "projected_ending_stock"
        ]
    )


def test_reserved_stock_reduces_ending_stock():
    without_reserved = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10] * 7,
    )

    with_reserved = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10] * 7,
        reserved_stock=20,
    )

    assert (
        with_reserved[
            "projected_ending_stock"
        ]
        == without_reserved[
            "projected_ending_stock"
        ] - 20
    )


def test_shortage_is_detected():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=20,
        predicted_demand=[10, 10, 10],
    )

    assert (
        result["expected_shortage_date"]
        is not None
    )

    assert result["shortage_days"] == 1


def test_no_shortage_when_stock_is_sufficient():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10, 10, 10],
    )

    assert (
        result["expected_shortage_date"]
        is None
    )

    assert result["shortage_days"] == 0


def test_safety_stock_breach():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=30,
        predicted_demand=[10, 10],
        safety_stock=20,
    )

    assert result[
        "safety_stock_breach"
    ] is True


def test_risk_is_critical_for_shortage():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=10,
        predicted_demand=[20, 20],
    )

    assert result["risk_level"] == "critical"


def test_risk_is_low_when_inventory_is_healthy():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=200,
        predicted_demand=[10] * 7,
        safety_stock=20,
    )

    assert result["risk_level"] == "low"


def test_forecast_point_fields():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10],
    )

    point = result["trajectory"][0]

    assert point["date"] == "2026-01-02"
    assert point["opening_stock"] == 100
    assert point["predicted_demand"] == 10
    assert point["closing_stock"] == 90
    assert point["shortage"] is False


def test_evaluate_projection():
    metrics = evaluate_projection(
        actual_stock=[
            100,
            90,
            80,
        ],
        projected_stock=[
            100,
            92,
            78,
        ],
    )

    assert set(metrics) == {
        "mae",
        "rmse",
        "mape",
        "wape",
    }

    for value in metrics.values():
        assert value >= 0


def test_evaluate_length_mismatch():
    with pytest.raises(ValueError):
        evaluate_projection(
            actual_stock=[100],
            projected_stock=[
                100,
                90,
            ],
        )


def test_predictor_class():
    predictor = (
        InventorySimulationPredictor()
    )

    result = predictor.predict(
        make_payload()
    )

    assert result["success"] is True


def test_invalid_facility_uuid():
    with pytest.raises(ValueError):
        simulate_inventory(
            facility_id="invalid",
            item_id="medicine-001",
            current_stock=100,
            predicted_demand=[10],
        )


def test_negative_current_stock():
    with pytest.raises(ValueError):
        simulate_inventory(
            facility_id=FACILITY_ID,
            item_id="medicine-001",
            current_stock=-1,
            predicted_demand=[10],
        )


def test_explanation_present():
    result = simulate_inventory(
        facility_id=FACILITY_ID,
        item_id="medicine-001",
        current_stock=100,
        predicted_demand=[10, 10],
    )

    assert len(
        result["explanation"]
    ) >= 3