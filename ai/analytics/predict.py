"""Inference interface for centralized healthcare analytics."""

from __future__ import annotations

from ai.common.base_model import BasePredictor

from .analytics import (
    calculate_analytics_summary,
    calculate_cost,
    calculate_historical_trend,
    calculate_utilization,
    calculate_wastage,
)
from .config import AnalyticsConfig, DEFAULT_CONFIG


class AnalyticsPredictor(BasePredictor):
    """Provide centralized healthcare analytics calculations."""

    def __init__(
        self,
        config: AnalyticsConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config

    def predict(
        self,
        payload: dict,
    ) -> dict:
        """Calculate the requested analytics operation."""

        operation = payload.get(
            "operation"
        )

        if operation == "historical_trend":
            result = calculate_historical_trend(
                periods=payload["periods"],
                values=payload["values"],
                metric_name=payload[
                    "metric_name"
                ],
            )

            return result.model_dump()

        if operation == "utilization":
            result = calculate_utilization(
                capacity=payload["capacity"],
                used=payload["used"],
                resource_name=payload[
                    "resource_name"
                ],
            )

            return result.model_dump()

        if operation == "cost":
            result = calculate_cost(
                quantity=payload["quantity"],
                cost_per_unit=payload[
                    "cost_per_unit"
                ],
                resource_name=payload[
                    "resource_name"
                ],
            )

            return result.model_dump()

        if operation == "wastage":
            result = calculate_wastage(
                supplied_quantity=payload[
                    "supplied_quantity"
                ],
                used_quantity=payload[
                    "used_quantity"
                ],
                resource_name=payload[
                    "resource_name"
                ],
                wastage_cost_per_unit=payload.get(
                    "wastage_cost_per_unit",
                    self.config.default_wastage_cost_per_unit,
                ),
            )

            return result.model_dump()

        if operation == "summary":
            result = calculate_analytics_summary(
                resource_name=payload[
                    "resource_name"
                ],
                capacity=payload["capacity"],
                used=payload["used"],
                quantity=payload["quantity"],
                cost_per_unit=payload[
                    "cost_per_unit"
                ],
                supplied_quantity=payload[
                    "supplied_quantity"
                ],
                wastage_used_quantity=payload[
                    "wastage_used_quantity"
                ],
                periods=payload["periods"],
                trend_values=payload[
                    "trend_values"
                ],
                wastage_cost_per_unit=payload.get(
                    "wastage_cost_per_unit",
                    self.config.default_wastage_cost_per_unit,
                ),
                config=self.config,
            )

            return result.model_dump()

        raise ValueError(
            "Unsupported analytics operation. "
            "Expected one of: historical_trend, "
            "utilization, cost, wastage, summary."
        )