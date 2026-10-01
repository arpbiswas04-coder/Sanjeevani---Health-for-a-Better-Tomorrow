"""Versioned, explainable weighted facility scores from normalized inputs."""

import json
import logging
from datetime import timedelta
from decimal import Decimal
from importlib.resources import files
from uuid import uuid4

from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

FACTORS = frozenset({"disease_growth", "resource_shortage", "bed_pressure", "workforce_shortage",
                     "vulnerable_population", "transport_disruption"})
LOGGER = logging.getLogger(__name__)


def _unit_value(value, path):
    number = nonnegative_number(value, path)
    if number > 1:
        raise ValidationError(f"{path} must be normalized to 0..1")
    return Decimal(str(value))


from optimization.common.telemetry import measured


@measured("optimizer", "emergency")
def score_emergency_priorities(request, policy=None, *, now=None):
    """Score complete, fresh facilities; preserve incomplete ones as unscored.

    All factors must mean higher value = higher operational pressure. Input
    normalization is owned by upstream models and must match the policy version.
    There is no imputation, clinical threshold, or resource allocation here.
    """
    if policy is None:
        policy = json.loads(files("optimization.emergency").joinpath("policy.example.json").read_text(encoding="utf-8"))
    rules = object_fields(policy, required={"policy_version", "normalization_version", "max_age_seconds", "weights"},
                          optional=set(), path="policy")
    policy_version = identifier(rules["policy_version"], "policy.policy_version")
    normalization = identifier(rules["normalization_version"], "policy.normalization_version")
    max_age = integer(rules["max_age_seconds"], "policy.max_age_seconds", 1)
    if max_age > 604800:
        raise ValidationError("policy.max_age_seconds must be at most 604800")
    raw_weights = object_fields(rules["weights"], required=FACTORS, optional=set(), path="policy.weights")
    weights = {factor: _unit_value(raw_weights[factor], f"policy.weights.{factor}") for factor in sorted(FACTORS)}
    if sum(weights.values()) != Decimal(1):
        raise ValidationError("policy weights must sum to exactly 1; no implicit normalization is performed")
    data = object_fields(request, required={"request_id", "snapshot_id", "captured_at", "normalization_version", "facilities"},
                         optional=set(), path="request")
    request_id = identifier(data["request_id"], "request_id")
    snapshot_id = identifier(data["snapshot_id"], "snapshot_id")
    if data["normalization_version"] != normalization:
        raise ValidationError("Input normalization_version does not match policy")
    current = utc_now(now)
    captured = utc_timestamp(data["captured_at"], "captured_at")
    if not 0 <= (current - captured).total_seconds() < max_age:
        raise ValidationError("Snapshot is stale or future-dated; refresh inputs")
    if not isinstance(data["facilities"], list) or len(data["facilities"]) > 1000:
        raise ValidationError("facilities must be an array of at most 1000 entries")
    scored, unscored, seen = [], [], set()
    for index, raw in enumerate(data["facilities"]):
        path = f"facilities[{index}]"
        facility = object_fields(raw, required={"facility_id", "signals"}, optional=set(), path=path)
        facility_id = identifier(facility["facility_id"], f"{path}.facility_id")
        if facility_id in seen:
            raise ValidationError("Duplicate facility ID")
        seen.add(facility_id)
        signals = object_fields(facility["signals"], required=set(), optional=FACTORS, path=f"{path}.signals")
        components, issues, expiries = [], [], [captured + timedelta(seconds=max_age)]
        total, coverage = Decimal(0), Decimal(0)
        for factor, weight in weights.items():
            signal = signals.get(factor)
            value, stamp, version, reason = None, None, None, None
            if signal is None:
                reason = "missing_signal"
            else:
                signal_path = f"{path}.signals.{factor}"
                record = object_fields(signal, required={"value", "observed_at", "source_version"}, optional=set(), path=signal_path)
                value = None if record["value"] is None else _unit_value(record["value"], f"{signal_path}.value")
                stamp = utc_timestamp(record["observed_at"], f"{signal_path}.observed_at")
                version = identifier(record["source_version"], f"{signal_path}.source_version")
                if value is None: reason = "missing_value"
                elif stamp > captured: reason = "observation_after_snapshot"
                elif (current - stamp).total_seconds() >= max_age: reason = "stale_signal"
            active = weight > 0
            contribution = Decimal(0) if not active else (None if reason else weight * value)
            if active:
                if reason:
                    issues.append({"factor": factor, "reason": reason})
                else:
                    total += contribution
                    coverage += weight
                    expiries.append(stamp + timedelta(seconds=max_age))
            components.append({"factor": factor, "weight": float(weight),
                               "value": float(value) if value is not None else None,
                               "contribution": float(contribution) if contribution is not None else None,
                               "status": "disabled" if not active else (reason or "valid"),
                               "observed_at": stamp.isoformat() if stamp is not None else None,
                               "source_version": version})
        row = {"facility_id": facility_id, "status": "unscored" if issues else "scored",
               "score": None if issues else float(total), "rank": None,
               "weight_coverage": float(coverage), "components": components, "issues": issues,
               "valid_until": None if issues else min(expiries).isoformat()}
        if issues:
            unscored.append(row)
        else:
            scored.append((total, row))
    scored.sort(key=lambda item: (-item[0], item[1]["facility_id"]))
    previous, rank = None, 0
    for position, (score, row) in enumerate(scored, start=1):
        if score != previous:
            rank = position
        row["rank"] = rank
        previous = score
    result = {"schema_version": "emergency-priority-1.0", "algorithm_version": "weighted-normalized-v1",
              "recommendation_id": str(uuid4()), "request_id": request_id, "snapshot_id": snapshot_id,
              "generated_at": current.isoformat(), "recommendation_only": True, "approval_required": True,
              "policy": {"policy_version": policy_version, "normalization_version": normalization,
                         "max_age_seconds": max_age, "weights": {key: float(value) for key, value in weights.items()}},
              "ranked_facilities": [row for _, row in scored],
              "unscored_facilities": sorted(unscored, key=lambda row: row["facility_id"]),
              "scored_count": len(scored), "unscored_count": len(unscored),
              "warnings": [
                  "Example weights and normalization contract are a prototype, not validated clinical triage.",
                  "Missing or stale required signals produce no score; unscored facilities are not low-priority facilities.",
                  "Compare scores only under the same policy, normalization and compatible forecast horizons.",
                  "This score does not allocate resources or bypass operational constraints and authorized approval.",
              ]}
    LOGGER.info("emergency_priority_scored scored=%d unscored=%d", len(scored), len(unscored))
    return result
