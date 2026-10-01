"""Feature generation for procurement demand forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd


def create_features(
    frame: pd.DataFrame,
    *,
    lookback_days: int = 14,
) -> pd.DataFrame:
    """Create leakage-safe demand features."""

    if "quantity_consumed" not in frame.columns:
        raise ValueError(
            "Expected quantity_consumed column."
        )

    result = frame.copy()

    result["day_of_week"] = result.index.dayofweek
    result["day_of_month"] = result.index.day
    result["month"] = result.index.month

    shifted = result["quantity_consumed"].shift(1)

    result["lag_1"] = result[
        "quantity_consumed"
    ].shift(1)

    result["lag_7"] = result[
        "quantity_consumed"
    ].shift(7)

    window = max(
        2,
        min(
            lookback_days,
            max(2, len(result)),
        ),
    )

    result["rolling_mean"] = shifted.rolling(
        window=window,
        min_periods=1,
    ).mean()

    result["rolling_std"] = shifted.rolling(
        window=window,
        min_periods=2,
    ).std()

    result["rolling_std"] = (
        result["rolling_std"]
        .fillna(0.0)
    )

    result["trend"] = (
        result["rolling_mean"]
        - shifted.shift(1)
    ).fillna(0.0)

    return result


def estimate_daily_demand(
    frame: pd.DataFrame,
    *,
    lookback_days: int = 14,
) -> float:
    """Estimate daily demand from recent historical consumption."""

    if frame.empty:
        raise ValueError(
            "Consumption history cannot be empty."
        )

    values = frame[
        "quantity_consumed"
    ].astype(float)

    recent = values.tail(
        min(
            lookback_days,
            len(values),
        )
    )

    if recent.empty:
        return 0.0

    mean_demand = float(
        recent.mean()
    )

    if len(recent) >= 3:
        x = np.arange(
            len(recent),
            dtype=float,
        )

        slope = float(
            np.polyfit(
                x,
                recent.to_numpy(dtype=float),
                1,
            )[0]
        )

        trend_adjustment = (
            slope * 0.5
        )
    else:
        trend_adjustment = 0.0

    estimated = max(
        0.0,
        mean_demand + trend_adjustment,
    )

    return float(estimated)