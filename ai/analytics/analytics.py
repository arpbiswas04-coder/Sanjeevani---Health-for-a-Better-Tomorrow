"""Core centralized healthcare analytics calculations."""

from __future__ import annotations

from collections.abc import Sequence

from .config import AnalyticsConfig, DEFAULT_CONFIG
from .schema import (
    AnalyticsSummaryResponse,
    CostResponse,
    HistoricalTrendPoint,
    HistoricalTrendResponse,
    UtilizationResponse,
    WastageResponse,
)


def _validate_non_negative_values(
    values: Sequence[float],
    *,
    name: str,
) -> list[float]:
    """Validate and normalize a non-negative numeric series."""

    if not values:
        raise ValueError(f"{name} cannot be empty.")

    normalized = [float(value) for value in values]

    if any(value < 0.0 for value in normalized):
        raise ValueError(
            f"{name} cannot contain negative values."
        )

    return normalized


def calculate_historical_trend(
    periods: Sequence[str],
    values: Sequence[float],
    *,
    metric_name: str,
) -> HistoricalTrendResponse:
    """Calculate historical totals, statistics, and change."""

    if not metric_name.strip():
        raise ValueError(
            "metric_name cannot be empty."
        )

    if not periods:
        raise ValueError(
            "periods cannot be empty."
        )

    if len(periods) != len(values):
        raise ValueError(
            "periods and values must contain the same "
            "number of items."
        )

    if any(
        not str(period).strip()
        for period in periods
    ):
        raise ValueError(
            "periods cannot contain empty values."
        )

    normalized = _validate_non_negative_values(
        values,
        name="values",
    )

    points = [
        HistoricalTrendPoint(
            period=str(period),
            value=value,
        )
        for period, value in zip(
            periods,
            normalized,
        )
    ]

    total = float(sum(normalized))
    average = float(total / len(normalized))
    minimum = float(min(normalized))
    maximum = float(max(normalized))

    if len(normalized) >= 2:
        change = float(
            normalized[-1] - normalized[0]
        )
    else:
        change = 0.0

    if normalized[0] == 0.0:
        percentage_change = (
            None
            if change != 0.0
            else 0.0
        )
    else:
        percentage_change = float(
            (change / abs(normalized[0]))
            * 100.0
        )

    return HistoricalTrendResponse(
        success=True,
        metric_name=metric_name,
        points=points,
        total=total,
        average=average,
        minimum=minimum,
        maximum=maximum,
        change=change,
        percentage_change=percentage_change,
    )


def calculate_utilization(
    capacity: float,
    used: float,
    *,
    resource_name: str,
) -> UtilizationResponse:
    """Calculate resource utilization."""

    if capacity < 0.0:
        raise ValueError(
            "capacity cannot be negative."
        )

    if used < 0.0:
        raise ValueError(
            "used cannot be negative."
        )

    if used > capacity:
        raise ValueError(
            "used cannot exceed capacity."
        )

    if not resource_name.strip():
        raise ValueError(
            "resource_name cannot be empty."
        )

    available = float(
        capacity - used
    )

    if capacity == 0.0:
        utilization_rate = 0.0
    else:
        utilization_rate = float(
            used / capacity
        )

    return UtilizationResponse(
        success=True,
        resource_name=resource_name,
        capacity=float(capacity),
        used=float(used),
        available=available,
        utilization_rate=utilization_rate,
        utilization_percentage=(
            utilization_rate * 100.0
        ),
    )


def calculate_cost(
    quantity: float,
    cost_per_unit: float,
    *,
    resource_name: str,
) -> CostResponse:
    """Calculate total and average resource cost."""

    if quantity < 0.0:
        raise ValueError(
            "quantity cannot be negative."
        )

    if cost_per_unit < 0.0:
        raise ValueError(
            "cost_per_unit cannot be negative."
        )

    if not resource_name.strip():
        raise ValueError(
            "resource_name cannot be empty."
        )

    total_cost = float(
        quantity * cost_per_unit
    )

    average_cost_per_unit = (
        float(cost_per_unit)
        if quantity > 0.0
        else 0.0
    )

    return CostResponse(
        success=True,
        resource_name=resource_name,
        quantity=float(quantity),
        cost_per_unit=float(cost_per_unit),
        total_cost=total_cost,
        average_cost_per_unit=average_cost_per_unit,
    )


def calculate_wastage(
    supplied_quantity: float,
    used_quantity: float,
    *,
    resource_name: str,
    wastage_cost_per_unit: float = (
        DEFAULT_CONFIG.default_wastage_cost_per_unit
    ),
) -> WastageResponse:
    """Calculate wastage quantity, rate, percentage, and cost."""

    if supplied_quantity < 0.0:
        raise ValueError(
            "supplied_quantity cannot be negative."
        )

    if used_quantity < 0.0:
        raise ValueError(
            "used_quantity cannot be negative."
        )

    if used_quantity > supplied_quantity:
        raise ValueError(
            "used_quantity cannot exceed "
            "supplied_quantity."
        )

    if wastage_cost_per_unit < 0.0:
        raise ValueError(
            "wastage_cost_per_unit cannot be negative."
        )

    if not resource_name.strip():
        raise ValueError(
            "resource_name cannot be empty."
        )

    wasted_quantity = float(
        supplied_quantity - used_quantity
    )

    if supplied_quantity == 0.0:
        wastage_rate = 0.0
    else:
        wastage_rate = float(
            wasted_quantity / supplied_quantity
        )

    wastage_cost = float(
        wasted_quantity * wastage_cost_per_unit
    )

    return WastageResponse(
        success=True,
        resource_name=resource_name,
        supplied_quantity=float(supplied_quantity),
        used_quantity=float(used_quantity),
        wasted_quantity=wasted_quantity,
        wastage_rate=wastage_rate,
        wastage_percentage=(
            wastage_rate * 100.0
        ),
        wastage_cost=wastage_cost,
    )


def calculate_analytics_summary(
    *,
    resource_name: str,
    capacity: float,
    used: float,
    quantity: float,
    cost_per_unit: float,
    supplied_quantity: float,
    wastage_used_quantity: float,
    periods: Sequence[str],
    trend_values: Sequence[float],
    wastage_cost_per_unit: float = (
        DEFAULT_CONFIG.default_wastage_cost_per_unit
    ),
    config: AnalyticsConfig = DEFAULT_CONFIG,
) -> AnalyticsSummaryResponse:
    """Calculate a combined analytics summary."""

    utilization = calculate_utilization(
        capacity=capacity,
        used=used,
        resource_name=resource_name,
    )

    cost = calculate_cost(
        quantity=quantity,
        cost_per_unit=cost_per_unit,
        resource_name=resource_name,
    )

    wastage = calculate_wastage(
        supplied_quantity=supplied_quantity,
        used_quantity=wastage_used_quantity,
        resource_name=resource_name,
        wastage_cost_per_unit=wastage_cost_per_unit,
    )

    trend = calculate_historical_trend(
        periods=periods,
        values=trend_values,
        metric_name=resource_name,
    )

    return AnalyticsSummaryResponse(
        success=True,
        resource_name=resource_name,
        utilization_rate=utilization.utilization_rate,
        total_cost=cost.total_cost,
        wastage_rate=wastage.wastage_rate,
        wastage_cost=wastage.wastage_cost,
        trend_change=trend.change,
        trend_percentage_change=(
            trend.percentage_change
        ),
        explanation=[
            (
                "Resource utilization is "
                f"{utilization.utilization_percentage:.2f}%."
            ),
            (
                "Calculated total cost is "
                f"{cost.total_cost:.2f}."
            ),
            (
                "Wastage rate is "
                f"{wastage.wastage_percentage:.2f}%."
            ),
            (
                "Historical trend change is "
                f"{trend.change:.2f}."
            ),
            (
                "Analytics calculation version: "
                f"{config.model_version}."
            ),
        ],
    )