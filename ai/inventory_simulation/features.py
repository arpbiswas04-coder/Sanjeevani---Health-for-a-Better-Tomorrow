"""Inventory simulation calculations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyInventoryState:
    """Calculated inventory state for one day."""

    opening_stock: float
    expected_incoming: float
    predicted_demand: float
    reserved_stock: float
    closing_stock: float


def calculate_daily_inventory(
    *,
    opening_stock: float,
    expected_incoming: float,
    predicted_demand: float,
    reserved_stock: float,
) -> DailyInventoryState:
    """Apply the inventory balance formula."""

    closing_stock = (
        opening_stock
        + expected_incoming
        - predicted_demand
        - reserved_stock
    )

    return DailyInventoryState(
        opening_stock=opening_stock,
        expected_incoming=expected_incoming,
        predicted_demand=predicted_demand,
        reserved_stock=reserved_stock,
        closing_stock=closing_stock,
    )


def calculate_projected_ending_stock(
    *,
    current_stock: float,
    expected_incoming: float,
    predicted_demand: float,
    reserved_stock: float,
) -> float:
    """Calculate projected stock after the complete horizon."""

    return (
        current_stock
        + expected_incoming
        - predicted_demand
        - reserved_stock
    )