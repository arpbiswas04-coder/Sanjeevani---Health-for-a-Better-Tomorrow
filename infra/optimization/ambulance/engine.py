"""Filter operational eligibility before deterministic ETA-based ranking."""

import logging
from datetime import timedelta
from uuid import uuid4

from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

LOGGER = logging.getLogger(__name__)


def _labels(value, path):
    if not isinstance(value, list) or len(value) > 100:
        raise ValidationError(f"{path} must be an array of at most 100 identifiers")
    labels = [identifier(item, path) for item in value]
    if len(set(labels)) != len(labels):
        raise ValidationError(f"{path} contains duplicate identifiers")
    return set(labels)


def _boolean(value, path):
    if type(value) is not bool:
        raise ValidationError(f"{path} must be boolean")
    return value


def recommend_ambulance(request, policy=None, *, now=None):
    """Recommend one ambulance and alternatives for one operational request.

    Required equipment and emergency capability labels come from authorized
    backend policy. This module does not infer clinical requirements or triage.
    """
    current = utc_now(now)
    data = object_fields(request, required={"request_id", "snapshot_id", "captured_at", "emergency_type",
                         "required_equipment", "patient_count", "candidates"}, optional=set(), path="request")
    rules = object_fields({} if policy is None else policy, required=set(),
                          optional={"max_age_seconds", "max_eta_minutes", "max_alternatives"}, path="policy")
    age_limit = integer(rules.get("max_age_seconds", 120), "policy.max_age_seconds", 1)
    if age_limit > 86400:
        raise ValidationError("policy.max_age_seconds must be at most 86400")
    alternative_limit = integer(rules.get("max_alternatives", 3), "policy.max_alternatives")
    if alternative_limit > 20:
        raise ValidationError("policy.max_alternatives must be at most 20")
    max_eta = rules.get("max_eta_minutes")
    if max_eta is not None:
        max_eta = nonnegative_number(max_eta, "policy.max_eta_minutes")
    request_id = identifier(data["request_id"], "request_id")
    snapshot_id = identifier(data["snapshot_id"], "snapshot_id")
    captured = utc_timestamp(data["captured_at"], "captured_at")
    if not 0 <= (current - captured).total_seconds() < age_limit:
        raise ValidationError("Snapshot is stale or future-dated; refresh before recommending")
    emergency = identifier(data["emergency_type"], "emergency_type")
    required = _labels(data["required_equipment"], "required_equipment")
    patients = integer(data["patient_count"], "patient_count", 1)
    if patients > 100:
        raise ValidationError("patient_count must be at most 100")
    if not isinstance(data["candidates"], list) or len(data["candidates"]) > 1000:
        raise ValidationError("candidates must be an array of at most 1000 entries")
    seen, eligible, rejected = set(), [], []
    for i, raw in enumerate(data["candidates"]):
        path = f"candidates[{i}]"
        candidate = object_fields(raw, required={"ambulance_id", "status", "reserved", "crew_ready",
            "serviceable", "patient_capacity", "equipment", "supported_emergency_types",
            "eta_minutes", "distance_km", "observed_at", "eta_observed_at"}, optional=set(), path=path)
        ambulance_id = identifier(candidate["ambulance_id"], f"{path}.ambulance_id")
        if ambulance_id in seen:
            raise ValidationError("Duplicate ambulance ID")
        seen.add(ambulance_id)
        status = identifier(candidate["status"], f"{path}.status")
        if status not in {"available", "busy", "offline", "maintenance"}:
            raise ValidationError(f"{path}.status is unsupported")
        reserved = _boolean(candidate["reserved"], f"{path}.reserved")
        crew = _boolean(candidate["crew_ready"], f"{path}.crew_ready")
        serviceable = _boolean(candidate["serviceable"], f"{path}.serviceable")
        capacity = integer(candidate["patient_capacity"], f"{path}.patient_capacity", 1)
        equipment = _labels(candidate["equipment"], f"{path}.equipment")
        types = _labels(candidate["supported_emergency_types"], f"{path}.supported_emergency_types")
        eta = None if candidate["eta_minutes"] is None else nonnegative_number(candidate["eta_minutes"], f"{path}.eta_minutes")
        distance = None if candidate["distance_km"] is None else nonnegative_number(candidate["distance_km"], f"{path}.distance_km")
        observed = utc_timestamp(candidate["observed_at"], f"{path}.observed_at")
        eta_observed = utc_timestamp(candidate["eta_observed_at"], f"{path}.eta_observed_at")
        reasons = []
        if status != "available": reasons.append("not_available")
        if reserved: reasons.append("already_reserved")
        if not crew: reasons.append("crew_not_ready")
        if not serviceable: reasons.append("not_serviceable")
        if capacity < patients: reasons.append("insufficient_patient_capacity")
        if required - equipment: reasons.append("missing_required_equipment")
        if emergency not in types: reasons.append("unsupported_emergency_type")
        if eta is None: reasons.append("eta_unavailable")
        elif max_eta is not None and eta > max_eta: reasons.append("eta_exceeds_policy")
        for stamp, label in ((observed, "availability"), (eta_observed, "eta")):
            if stamp > captured:
                reasons.append(f"{label}_timestamp_after_snapshot")
            elif (current - stamp).total_seconds() >= age_limit:
                reasons.append(f"stale_{label}")
        if reasons:
            rejected.append({"ambulance_id": ambulance_id, "reasons": reasons,
                             "missing_equipment": sorted(required - equipment)})
        else:
            eligible.append({"ambulance_id": ambulance_id, "eta_minutes": eta, "distance_km": distance,
                             "valid_until": min(captured, observed, eta_observed) + timedelta(seconds=age_limit),
                             "reason": "Meets operational requirements; ranked by ETA, distance, then ID"})
    eligible.sort(key=lambda c: (c["eta_minutes"], float("inf") if c["distance_km"] is None else c["distance_km"], c["ambulance_id"]))
    selected = eligible[:alternative_limit + 1]
    valid_until = min((c["valid_until"] for c in selected), default=captured + timedelta(seconds=age_limit))
    for rank, candidate in enumerate(selected, start=1):
        candidate["rank"] = rank
        candidate["valid_until"] = candidate["valid_until"].isoformat()
    result = {"schema_version": "ambulance-1.0", "algorithm_version": "eligibility-eta-v1",
              "recommendation_id": str(uuid4()), "request_id": request_id, "snapshot_id": snapshot_id,
              "generated_at": current.isoformat(), "valid_until": valid_until.isoformat(),
              "recommendation_only": True, "approval_required": True,
              "status": "recommended" if selected else "no_eligible_ambulance",
              "recommended": selected[0] if selected else None, "alternatives": selected[1:],
              "eligible_count": len(eligible), "alternatives_omitted": max(0, len(eligible) - len(selected)),
              "rejected_candidates": sorted(rejected, key=lambda c: c["ambulance_id"]),
              "emergency_type": emergency, "required_equipment": sorted(required), "patient_count": patients,
              "policy": {"max_age_seconds": age_limit, "max_eta_minutes": max_eta, "max_alternatives": alternative_limit},
              "warnings": ["Requirements and capability labels must come from authorized operational policy.",
                           "Availability, crew, equipment and ETA must be rechecked and the vehicle atomically reserved after approval.",
                           "Single-request recommendation only; this does not coordinate simultaneous requests or dispatch a vehicle."]}
    LOGGER.info("ambulance_recommendation status=%s eligible=%d rejected=%d", result["status"], len(eligible), len(rejected))
    return result
