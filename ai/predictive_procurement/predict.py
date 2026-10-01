"""Inference for predictive procurement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ai.common.base_model import BasePredictor

from .config import (
    DEFAULT_CONFIG,
    PredictiveProcurementConfig,
)
from .data import (
    clean_consumption_history,
    records_to_dataframe,
    validate_history_length,
)
from .schema import (
    ProcurementForecastPoint,
    ProcurementRequest,
    ProcurementResponse,
)
from .train import (
    ProcurementDemandModel,
    train_model,
)


class PredictiveProcurementPredictor(
    BasePredictor
):
    """Generate inventory-aware procurement recommendations."""

    def __init__(
        self,
        config: PredictiveProcurementConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config
        self.model: ProcurementDemandModel | None = None

    def fit(
        self,
        frame,
    ) -> ProcurementDemandModel:
        """Fit the demand estimation model."""

        validate_history_length(
            frame,
            self.config.min_history_points,
        )

        cleaned = clean_consumption_history(
            frame
        )

        self.model = train_model(
            cleaned,
            config=self.config,
        )

        return self.model

    def predict(
        self,
        payload: dict,
    ) -> dict:
        """Generate a procurement recommendation."""

        request = ProcurementRequest.model_validate(
            payload
        )

        frame = records_to_dataframe(
            request.history
        )

        frame = clean_consumption_history(
            frame
        )

        model = self.fit(frame)

        daily_demand = (
            model.average_daily_demand
        )

        horizon = request.horizon_days

        expected_demand = (
            daily_demand * horizon
        )

        safety_stock = (
            daily_demand
            * self.config.safety_stock_days
        )

        available_stock = max(
            0.0,
            request.current_stock
            + request.expected_incoming
            - request.reserved_stock,
        )

        required_stock = (
            expected_demand
            + safety_stock
        )

        suggested_procurement = max(
            0.0,
            required_stock - available_stock,
        )

        forecast: list[
            ProcurementForecastPoint
        ] = []

        projected_stock = available_stock
        cumulative_demand = 0.0
        shortage_date: str | None = None

        last_timestamp = frame.index[-1]

        for day in range(1, horizon + 1):
            forecast_date = (
                last_timestamp
                + timedelta(days=day)
            )

            predicted_demand = daily_demand

            cumulative_demand += (
                predicted_demand
            )

            projected_stock = (
                available_stock
                - cumulative_demand
            )

            shortage = (
                projected_stock
                < self.config.shortage_threshold
            )

            if (
                shortage
                and shortage_date is None
            ):
                shortage_date = (
                    forecast_date.date().isoformat()
                )

            forecast.append(
                ProcurementForecastPoint(
                    date=forecast_date.date().isoformat(),
                    predicted_demand=predicted_demand,
                    cumulative_demand=cumulative_demand,
                    projected_stock=projected_stock,
                    shortage=shortage,
                )
            )

        projected_stock_after_horizon = (
            available_stock
            - expected_demand
        )

        if shortage_date is not None:
            shortage_risk = "critical"
        elif projected_stock_after_horizon < safety_stock:
            shortage_risk = "high"
        elif (
            projected_stock_after_horizon
            < safety_stock * 2
        ):
            shortage_risk = "moderate"
        else:
            shortage_risk = "low"

        estimated_cost = (
            suggested_procurement
            * request.unit_cost
        )

        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

        explanation = [
            (
                "Expected demand is estimated from "
                "recent historical consumption and "
                "its short-term trend."
            ),
            (
                "Suggested procurement covers the "
                "forecast horizon plus configured "
                "safety stock."
            ),
            (
                "Current stock, expected incoming stock, "
                "and reserved stock are included when "
                "calculating the procurement gap."
            ),
            (
                "The expected shortage date indicates "
                "when projected available stock falls "
                "below the configured shortage threshold."
            ),
            (
                "This module provides a predictive "
                "procurement recommendation; it does "
                "not create or approve purchase orders."
            ),
        ]

        response = ProcurementResponse(
            success=True,
            facility_id=request.facility_id,
            item_id=request.item_id,
            model_version=model.model_version,
            horizon_days=horizon,
            average_daily_demand=daily_demand,
            expected_demand=expected_demand,
            current_stock=request.current_stock,
            expected_incoming=request.expected_incoming,
            reserved_stock=request.reserved_stock,
            safety_stock=safety_stock,
            projected_stock_after_horizon=(
                projected_stock_after_horizon
            ),
            suggested_procurement_quantity=(
                suggested_procurement
            ),
            expected_shortage_date=shortage_date,
            shortage_risk=shortage_risk,
            estimated_procurement_cost=estimated_cost,
            forecast=forecast,
            explanation=explanation,
            generated_at=generated_at,
        )

        return response.model_dump()


def predict_procurement(
    *,
    facility_id: str,
    item_id: str,
    current_stock: float,
    history: list[dict],
    expected_incoming: float = 0.0,
    reserved_stock: float = 0.0,
    unit_cost: float = 0.0,
    horizon_days: int = 7,
    config: PredictiveProcurementConfig = DEFAULT_CONFIG,
) -> dict:
    """Convenience function for procurement prediction."""

    predictor = PredictiveProcurementPredictor(
        config=config
    )

    payload = {
        "facility_id": facility_id,
        "item_id": item_id,
        "current_stock": current_stock,
        "expected_incoming": expected_incoming,
        "reserved_stock": reserved_stock,
        "unit_cost": unit_cost,
        "history": history,
        "horizon_days": horizon_days,
    }

    return predictor.predict(payload)