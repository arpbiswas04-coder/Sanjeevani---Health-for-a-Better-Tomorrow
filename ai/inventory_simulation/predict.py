"""Inference for inventory simulation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ai.common.base_model import BasePredictor

from .config import (
    DEFAULT_CONFIG,
    InventorySimulationConfig,
)
from .data import (
    normalize_incoming,
    validate_demand,
)
from .features import (
    calculate_daily_inventory,
)
from .schema import (
    InventorySimulationPoint,
    InventorySimulationRequest,
    InventorySimulationResponse,
)
from .train import (
    InventorySimulationModel,
    train_model,
)


class InventorySimulationPredictor(
    BasePredictor
):
    """Simulate future inventory levels."""

    def __init__(
        self,
        config: InventorySimulationConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config
        self.model: InventorySimulationModel | None = None

    def fit(self) -> InventorySimulationModel:
        """Initialize the deterministic simulation model."""

        self.model = train_model(
            config=self.config
        )

        return self.model

    def predict(
        self,
        payload: dict,
    ) -> dict:
        """Generate an inventory trajectory."""

        request = (
            InventorySimulationRequest.model_validate(
                payload
            )
        )

        model = self.fit()

        demand = validate_demand(
            request.predicted_demand
        )

        incoming = normalize_incoming(
            request.expected_incoming,
            len(demand),
        )

        start = datetime.fromisoformat(
            request.start_date.replace(
                "Z",
                "+00:00",
            )
        )

        opening_stock = request.current_stock

        trajectory: list[
            InventorySimulationPoint
        ] = []

        shortage_date: str | None = None
        shortage_days = 0
        minimum_stock = float("inf")

        for index, predicted_demand in enumerate(
            demand
        ):
            current_date = (
                start
                + timedelta(days=index + 1)
            )

            daily_reserved_stock = (
                request.reserved_stock
                if index == 0
                else 0.0
            )

            state = calculate_daily_inventory(
                opening_stock=opening_stock,
                expected_incoming=incoming[index],
                predicted_demand=predicted_demand,
                reserved_stock=daily_reserved_stock,
            )

            closing_stock = state.closing_stock

            minimum_stock = min(
                minimum_stock,
                closing_stock,
            )

            shortage = (
                closing_stock
                < self.config.shortage_threshold
            )

            low_stock = (
                closing_stock
                < request.safety_stock
            )

            if shortage:
                shortage_days += 1

                if shortage_date is None:
                    shortage_date = (
                        current_date.date()
                        .isoformat()
                    )

            trajectory.append(
                InventorySimulationPoint(
                    date=current_date.date().isoformat(),
                    opening_stock=state.opening_stock,
                    expected_incoming=(
                        state.expected_incoming
                    ),
                    predicted_demand=(
                        state.predicted_demand
                    ),
                    reserved_stock=(
                        state.reserved_stock
                    ),
                    closing_stock=closing_stock,
                    shortage=shortage,
                    low_stock=low_stock,
                )
            )

            opening_stock = closing_stock

        total_demand = sum(demand)
        total_incoming = sum(incoming)

        projected_ending_stock = (
            request.current_stock
            + total_incoming
            - total_demand
            - request.reserved_stock
        )

        safety_stock_breach = (
            minimum_stock
            < request.safety_stock
        )

        if shortage_days > 0:
            risk_level = "critical"
        elif safety_stock_breach:
            risk_level = "high"
        elif (
            minimum_stock
            < request.safety_stock * 2
        ):
            risk_level = "moderate"
        else:
            risk_level = "low"

        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

        explanation = [
            (
                "Future inventory is simulated using "
                "current stock, expected incoming stock, "
                "predicted demand, and reserved stock."
            ),
            (
                "Reserved stock is deducted on the first "
                "simulation day to prevent it from being "
                "treated as available inventory."
            ),
            (
                "The projected trajectory identifies "
                "days where stock falls below zero or "
                "below the configured safety-stock level."
            ),
            (
                "This simulation consumes predicted demand; "
                "it does not independently forecast demand."
            ),
            (
                "This module is a planning simulation and "
                "does not create or approve purchase orders."
            ),
        ]

        response = InventorySimulationResponse(
            success=True,
            facility_id=request.facility_id,
            item_id=request.item_id,
            model_version=model.model_version,
            initial_stock=request.current_stock,
            reserved_stock=request.reserved_stock,
            total_predicted_demand=total_demand,
            total_expected_incoming=total_incoming,
            projected_ending_stock=(
                projected_ending_stock
            ),
            minimum_projected_stock=minimum_stock,
            expected_shortage_date=shortage_date,
            shortage_days=shortage_days,
            safety_stock=request.safety_stock,
            safety_stock_breach=safety_stock_breach,
            risk_level=risk_level,
            trajectory=trajectory,
            explanation=explanation,
            generated_at=generated_at,
        )

        return response.model_dump()


def simulate_inventory(
    *,
    facility_id: str,
    item_id: str,
    current_stock: float,
    predicted_demand: list[float],
    expected_incoming: list[float] | None = None,
    reserved_stock: float = 0.0,
    start_date: str = (
        "2026-01-01T00:00:00+00:00"
    ),
    safety_stock: float = 0.0,
    config: InventorySimulationConfig = DEFAULT_CONFIG,
) -> dict:
    """Convenience function for inventory simulation."""

    predictor = InventorySimulationPredictor(
        config=config
    )

    payload = {
        "facility_id": facility_id,
        "item_id": item_id,
        "current_stock": current_stock,
        "reserved_stock": reserved_stock,
        "predicted_demand": predicted_demand,
        "expected_incoming": (
            expected_incoming or []
        ),
        "start_date": start_date,
        "safety_stock": safety_stock,
    }

    return predictor.predict(payload)