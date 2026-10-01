"""Inference for disease intelligence and outbreak early warning."""

from __future__ import annotations

import math
import uuid

import pandas as pd

from ai.common.types import (
    RiskLevel,
    now_utc_iso8601,
)
from ai.disease_intelligence.config import (
    DEFAULT_CONFIG,
    DiseaseIntelligenceConfig,
)
from ai.disease_intelligence.data import (
    aggregate_daily_cases,
    validate_and_load_cases,
)
from ai.disease_intelligence.features import (
    build_disease_features,
)
from ai.disease_intelligence.schema import (
    DiseaseCluster,
    DiseaseIntelligenceRequest,
    DiseaseIntelligenceResponse,
    DiseaseTrendPoint,
)
from ai.disease_intelligence.train import (
    DiseaseTrainingResult,
    calculate_surge_probability,
)


def _risk_from_probability(
    probability: float,
    config: DiseaseIntelligenceConfig,
) -> RiskLevel:
    """Map surge probability to the canonical risk level."""

    if (
        probability
        >= config.critical_surge_probability
    ):
        return RiskLevel.CRITICAL

    if (
        probability
        >= config.high_surge_probability
    ):
        return RiskLevel.HIGH

    if probability >= 0.40:
        return RiskLevel.MODERATE

    return RiskLevel.LOW


def _haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate geographic distance in kilometres."""

    radius = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )
    delta_lon = math.radians(
        lon2 - lon1
    )

    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    return float(
        radius
        * 2
        * math.asin(
            math.sqrt(
                min(1.0, value)
            )
        )
    )


class DiseaseIntelligencePredictor:
    """Operational outbreak early-warning predictor."""

    def __init__(
        self,
        training_result: DiseaseTrainingResult,
        config: DiseaseIntelligenceConfig = DEFAULT_CONFIG,
    ) -> None:
        self.training_result = training_result
        self.config = config

    def _build_clusters(
        self,
        frame: pd.DataFrame,
        disease: str,
    ) -> list[DiseaseCluster]:
        """Identify simple geographic case clusters."""

        disease_frame = frame[
            frame["disease"] == disease
        ].copy()

        if disease_frame.empty:
            return []

        latest_date = disease_frame["date"].max()

        latest = disease_frame[
            disease_frame["date"] == latest_date
        ]

        if latest.empty:
            return []

        coordinates = latest[
            [
                "latitude",
                "longitude",
                "case_count",
            ]
        ].reset_index(drop=True)

        clusters: list[DiseaseCluster] = []
        used: set[int] = set()
        cluster_number = 0

        for index, row in coordinates.iterrows():
            if index in used:
                continue

            members: list[int] = []

            for other_index, other in coordinates.iterrows():
                distance = _haversine_km(
                    float(row["latitude"]),
                    float(row["longitude"]),
                    float(other["latitude"]),
                    float(other["longitude"]),
                )

                if distance <= 25.0:
                    members.append(other_index)

            used.update(members)

            cluster_rows = coordinates.iloc[
                members
            ]

            total_cases = int(
                cluster_rows["case_count"].sum()
            )

            cluster_lat = float(
                cluster_rows["latitude"].mean()
            )

            cluster_lon = float(
                cluster_rows["longitude"].mean()
            )

            radius = max(
                [
                    _haversine_km(
                        cluster_lat,
                        cluster_lon,
                        float(lat),
                        float(lon),
                    )
                    for lat, lon in zip(
                        cluster_rows["latitude"],
                        cluster_rows["longitude"],
                    )
                ]
                or [0.0]
            )

            cluster_signal = min(
                total_cases
                / max(
                    self.training_result.baseline_mean,
                    1.0,
                ),
                1.0,
            )

            clusters.append(
                DiseaseCluster(
                    cluster_id=(
                        f"cluster-{cluster_number}"
                    ),
                    disease=disease,
                    latitude=cluster_lat,
                    longitude=cluster_lon,
                    case_count=total_cases,
                    member_count=len(members),
                    radius_km=float(radius),
                    risk_level=_risk_from_probability(
                        cluster_signal,
                        self.config,
                    ),
                )
            )

            cluster_number += 1

        return clusters

    def predict(
        self,
        request: DiseaseIntelligenceRequest,
    ) -> DiseaseIntelligenceResponse:
        """Generate disease trend and outbreak-warning intelligence."""

        records = [
            item.model_dump()
            for item in request.history
            if item.disease == request.disease
        ]

        if len(records) < self.config.min_history_points:
            raise ValueError(
                "Insufficient disease history"
            )

        frame = validate_and_load_cases(records)

        daily = aggregate_daily_cases(frame)

        disease_frame = daily[
            daily["disease"] == request.disease
        ].copy()

        if (
            len(disease_frame)
            < self.config.min_history_points
        ):
            raise ValueError(
                "Insufficient daily disease history"
            )

        features = build_disease_features(
            disease_frame,
            growth_window=self.config.growth_window,
        )

        usable = features.dropna(
            subset=["rolling_mean"]
        )

        if usable.empty:
            raise ValueError(
                "No usable disease trend data"
            )

        trajectory: list[DiseaseTrendPoint] = []

        for _, row in usable.iterrows():
            probability = (
                calculate_surge_probability(
                    float(row["growth_rate"]),
                    float(row["anomaly_score"]),
                    self.config,
                )
            )

            trajectory.append(
                DiseaseTrendPoint(
                    timestamp=row[
                        "date"
                    ].isoformat(),
                    disease=request.disease,
                    observed_cases=int(
                        row["case_count"]
                    ),
                    expected_cases=float(
                        max(
                            row["rolling_mean"],
                            0.0,
                        )
                    ),
                    growth_rate=float(
                        row["growth_rate"]
                    ),
                    anomaly_score=float(
                        row["anomaly_score"]
                    ),
                    surge_probability=probability,
                    risk_level=_risk_from_probability(
                        probability,
                        self.config,
                    ),
                )
            )

        latest = trajectory[-1]

        clusters = self._build_clusters(
            frame,
            request.disease,
        )

        explanation = [
            (
                "Surge probability combines recent "
                "case growth and statistical anomaly evidence."
            ),
            (
                "Geographic clusters are based on "
                "spatial proximity of observed cases."
            ),
            (
                "This output is operational early-warning "
                "intelligence and is not a disease diagnosis."
            ),
        ]

        return DiseaseIntelligenceResponse(
            success=True,
            prediction_id=str(uuid.uuid4()),
            facility_id=request.facility_id,
            disease=request.disease,
            model_version=(
                self.training_result.model_version
            ),
            generated_at=now_utc_iso8601(),
            current_growth_rate=(
                latest.growth_rate
            ),
            surge_probability=(
                latest.surge_probability
            ),
            risk_level=latest.risk_level,
            trajectory=trajectory,
            clusters=clusters,
            confidence=(
                self.training_result.confidence
            ),
            explanation=explanation,
        )