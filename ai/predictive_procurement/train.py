"""Demand estimation model for predictive procurement."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import (
    DEFAULT_CONFIG,
    PredictiveProcurementConfig,
)
from .features import estimate_daily_demand


@dataclass
class ProcurementDemandModel:
    """Fitted procurement demand model."""

    average_daily_demand: float
    recent_daily_demand: float
    trend_adjustment: float
    model_version: str


def train_model(
    frame: pd.DataFrame,
    *,
    config: PredictiveProcurementConfig = DEFAULT_CONFIG,
) -> ProcurementDemandModel:
    """Estimate future daily demand from historical consumption."""

    if frame.empty:
        raise ValueError(
            "Consumption history cannot be empty."
        )

    recent = frame[
        "quantity_consumed"
    ].tail(config.lookback_days)

    recent_mean = float(
        recent.mean()
    )

    estimated = estimate_daily_demand(
        frame,
        lookback_days=config.lookback_days,
    )

    trend_adjustment = (
        estimated - recent_mean
    )

    return ProcurementDemandModel(
        average_daily_demand=estimated,
        recent_daily_demand=recent_mean,
        trend_adjustment=trend_adjustment,
        model_version=config.model_version,
    )