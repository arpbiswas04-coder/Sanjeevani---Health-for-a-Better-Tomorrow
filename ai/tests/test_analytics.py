"""Tests for centralized healthcare analytics."""

from __future__ import annotations

import pytest

from ai.analytics.analytics import (
    calculate_analytics_summary,
    calculate_cost,
    calculate_historical_trend,
    calculate_utilization,
    calculate_wastage,
)
from ai.analytics.predict import AnalyticsPredictor


def test_historical_trend_calculates_statistics() -> None:
    result = calculate_historical_trend(
        periods=["Jan", "Feb", "Mar"],
        values=[100.0, 120.0, 150.0],
        metric_name="patient_visits",
    )

    assert result.success is True
    assert result.total == pytest.approx(370.0)
    assert result.average == pytest.approx(
        123.3333333
    )
    assert result.minimum == pytest.approx(100.0)
    assert result.maximum == pytest.approx(150.0)
    assert result.change == pytest.approx(50.0)
    assert result.percentage_change == pytest.approx(
        50.0
    )


def test_historical_trend_handles_zero_baseline() -> None:
    result = calculate_historical_trend(
        periods=["Jan", "Feb"],
        values=[0.0, 10.0],
        metric_name="cases",
    )

    assert result.change == pytest.approx(10.0)
    assert result.percentage_change is None


def test_historical_trend_handles_single_point() -> None:
    result = calculate_historical_trend(
        periods=["Jan"],
        values=[100.0],
        metric_name="cases",
    )

    assert result.change == pytest.approx(0.0)
    assert result.percentage_change == pytest.approx(
        0.0
    )


def test_historical_trend_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        calculate_historical_trend(
            periods=["Jan", "Feb"],
            values=[10.0],
            metric_name="cases",
        )


def test_historical_trend_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        calculate_historical_trend(
            periods=["Jan", "Feb"],
            values=[10.0, -1.0],
            metric_name="cases",
        )


def test_historical_trend_rejects_empty_metric_name() -> None:
    with pytest.raises(ValueError):
        calculate_historical_trend(
            periods=["Jan"],
            values=[10.0],
            metric_name="",
        )


def test_utilization_calculation() -> None:
    result = calculate_utilization(
        capacity=100.0,
        used=75.0,
        resource_name="general_ward",
    )

    assert result.success is True
    assert result.available == pytest.approx(25.0)
    assert result.utilization_rate == pytest.approx(
        0.75
    )
    assert result.utilization_percentage == pytest.approx(
        75.0
    )


def test_utilization_rejects_used_above_capacity() -> None:
    with pytest.raises(ValueError):
        calculate_utilization(
            capacity=100.0,
            used=101.0,
            resource_name="beds",
        )


def test_utilization_rejects_negative_capacity() -> None:
    with pytest.raises(ValueError):
        calculate_utilization(
            capacity=-1.0,
            used=0.0,
            resource_name="beds",
        )


def test_zero_capacity_has_zero_utilization() -> None:
    result = calculate_utilization(
        capacity=0.0,
        used=0.0,
        resource_name="beds",
    )

    assert result.utilization_rate == pytest.approx(
        0.0
    )


def test_cost_calculation() -> None:
    result = calculate_cost(
        quantity=100.0,
        cost_per_unit=25.0,
        resource_name="medicine",
    )

    assert result.total_cost == pytest.approx(
        2500.0
    )
    assert result.average_cost_per_unit == pytest.approx(
        25.0
    )


def test_cost_zero_quantity() -> None:
    result = calculate_cost(
        quantity=0.0,
        cost_per_unit=25.0,
        resource_name="medicine",
    )

    assert result.total_cost == pytest.approx(0.0)
    assert result.average_cost_per_unit == pytest.approx(
        0.0
    )


def test_cost_rejects_negative_quantity() -> None:
    with pytest.raises(ValueError):
        calculate_cost(
            quantity=-1.0,
            cost_per_unit=25.0,
            resource_name="medicine",
        )


def test_cost_rejects_negative_unit_cost() -> None:
    with pytest.raises(ValueError):
        calculate_cost(
            quantity=10.0,
            cost_per_unit=-25.0,
            resource_name="medicine",
        )


def test_wastage_calculation() -> None:
    result = calculate_wastage(
        supplied_quantity=100.0,
        used_quantity=80.0,
        resource_name="medicine",
        wastage_cost_per_unit=10.0,
    )

    assert result.wasted_quantity == pytest.approx(
        20.0
    )
    assert result.wastage_rate == pytest.approx(
        0.20
    )
    assert result.wastage_percentage == pytest.approx(
        20.0
    )
    assert result.wastage_cost == pytest.approx(
        200.0
    )


def test_wastage_rejects_usage_above_supply() -> None:
    with pytest.raises(ValueError):
        calculate_wastage(
            supplied_quantity=100.0,
            used_quantity=110.0,
            resource_name="medicine",
        )


def test_wastage_rejects_negative_supply() -> None:
    with pytest.raises(ValueError):
        calculate_wastage(
            supplied_quantity=-1.0,
            used_quantity=0.0,
            resource_name="medicine",
        )


def test_zero_supply_has_zero_wastage_rate() -> None:
    result = calculate_wastage(
        supplied_quantity=0.0,
        used_quantity=0.0,
        resource_name="medicine",
    )

    assert result.wastage_rate == pytest.approx(
        0.0
    )


def test_combined_analytics_summary() -> None:
    result = calculate_analytics_summary(
        resource_name="general_ward",
        capacity=100.0,
        used=70.0,
        quantity=50.0,
        cost_per_unit=20.0,
        supplied_quantity=100.0,
        wastage_used_quantity=90.0,
        periods=["Jan", "Feb", "Mar"],
        trend_values=[50.0, 60.0, 70.0],
        wastage_cost_per_unit=5.0,
    )

    assert result.success is True
    assert result.utilization_rate == pytest.approx(
        0.70
    )
    assert result.total_cost == pytest.approx(
        1000.0
    )
    assert result.wastage_rate == pytest.approx(
        0.10
    )
    assert result.wastage_cost == pytest.approx(
        50.0
    )
    assert result.trend_change == pytest.approx(
        20.0
    )


def test_predictor_historical_trend() -> None:
    predictor = AnalyticsPredictor()

    result = predictor.predict(
        {
            "operation": "historical_trend",
            "metric_name": "admissions",
            "periods": ["Jan", "Feb"],
            "values": [100.0, 125.0],
        }
    )

    assert result["success"] is True
    assert result["change"] == pytest.approx(
        25.0
    )


def test_predictor_utilization() -> None:
    predictor = AnalyticsPredictor()

    result = predictor.predict(
        {
            "operation": "utilization",
            "resource_name": "icu",
            "capacity": 50.0,
            "used": 40.0,
        }
    )

    assert result["success"] is True
    assert result["utilization_percentage"] == pytest.approx(
        80.0
    )


def test_predictor_cost() -> None:
    predictor = AnalyticsPredictor()

    result = predictor.predict(
        {
            "operation": "cost",
            "resource_name": "medicine",
            "quantity": 10.0,
            "cost_per_unit": 100.0,
        }
    )

    assert result["success"] is True
    assert result["total_cost"] == pytest.approx(
        1000.0
    )


def test_predictor_wastage() -> None:
    predictor = AnalyticsPredictor()

    result = predictor.predict(
        {
            "operation": "wastage",
            "resource_name": "medicine",
            "supplied_quantity": 100.0,
            "used_quantity": 90.0,
            "wastage_cost_per_unit": 5.0,
        }
    )

    assert result["success"] is True
    assert result["wasted_quantity"] == pytest.approx(
        10.0
    )


def test_predictor_summary() -> None:
    predictor = AnalyticsPredictor()

    result = predictor.predict(
        {
            "operation": "summary",
            "resource_name": "icu",
            "capacity": 50.0,
            "used": 40.0,
            "quantity": 20.0,
            "cost_per_unit": 100.0,
            "supplied_quantity": 100.0,
            "wastage_used_quantity": 95.0,
            "periods": ["Jan", "Feb"],
            "trend_values": [20.0, 25.0],
            "wastage_cost_per_unit": 10.0,
        }
    )

    assert result["success"] is True
    assert result["utilization_rate"] == pytest.approx(
        0.80
    )
    assert result["total_cost"] == pytest.approx(
        2000.0
    )
    assert result["wastage_rate"] == pytest.approx(
        0.05
    )


def test_predictor_rejects_unknown_operation() -> None:
    predictor = AnalyticsPredictor()

    with pytest.raises(ValueError):
        predictor.predict(
            {
                "operation": "unknown",
            }
        )