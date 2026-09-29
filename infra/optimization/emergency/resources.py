"""Join fresh operational scores to constrained transport recommendations."""

from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from uuid import uuid4

from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, object_fields
from optimization.emergency import score_emergency_priorities
from optimization.transport import recommend_transport

PRIORITY_SCALE = 1_000_000


def recommend_emergency_resources(request, score_policy=None, *, max_inventory_age_seconds=300,
                                  time_limit_seconds=5, min_expiry_days=1, now=None):
    """Compute priorities from raw signals, then allocate a single medicine.

    Never accepts a caller-supplied score as authoritative. Complete destination
    coverage is required before allocating; unresolved data issues block the plan.
    """
    data = object_fields(request, required={"transport_request", "risk_request", "inventory_captured_at"},
                         optional=set(), path="request")
    current = utc_now(now)
    age_limit = integer(max_inventory_age_seconds, "max_inventory_age_seconds", 1)
    if age_limit > 86400:
        raise ValidationError("max_inventory_age_seconds must be at most 86400")
    captured = utc_timestamp(data["inventory_captured_at"], "inventory_captured_at")
    if not 0 <= (current - captured).total_seconds() < age_limit:
        raise ValidationError("Inventory snapshot is stale or future-dated")
    transport = data["transport_request"]
    if not isinstance(transport, dict) or not isinstance(transport.get("destinations"), list):
        raise ValidationError("transport_request must include destinations")
    request_id = identifier(transport.get("request_id"), "transport_request.request_id")
    snapshot_id = identifier(transport.get("inventory_snapshot_id"), "transport_request.inventory_snapshot_id")
    destination_ids = set()
    for index, value in enumerate(transport["destinations"]):
        destination = object_fields(value, required={"facility_id", "required_quantity"}, optional=set(), path=f"destinations[{index}]")
        facility = identifier(destination["facility_id"], "destination.facility_id")
        integer(destination["required_quantity"], "destination.required_quantity")
        if facility in destination_ids:
            raise ValidationError("Duplicate destination facility")
        destination_ids.add(facility)
    scores = score_emergency_priorities(data["risk_request"], score_policy, now=current)
    if scores["request_id"] != request_id:
        raise ValidationError("Transport and risk request IDs must match")
    scored = {row["facility_id"]: row for row in scores["ranked_facilities"]}
    unscored = {row["facility_id"]: row for row in scores["unscored_facilities"]}
    if (set(scored) | set(unscored)) - destination_ids:
        raise ValidationError("Risk request contains facilities outside transport destinations")
    blocked = [{"facility_id": facility, "reason": "unscored_priority" if facility in unscored else "missing_priority",
                "issues": unscored.get(facility, {}).get("issues", [])}
               for facility in sorted(destination_ids - set(scored))]
    result = {"schema_version": "emergency-resources-1.0", "recommendation_id": str(uuid4()),
              "request_id": request_id, "inventory_snapshot_id": snapshot_id,
              "generated_at": current.isoformat(), "recommendation_only": True, "approval_required": True,
              "status": "needs_data_review" if blocked else "ready", "valid_until": None,
              "scoring": scores, "blocked_facilities": blocked, "allocation": None,
              "allocation_policy": {"version": "fulfillment-priority-cost-v1", "priority_scale": PRIORITY_SCALE,
                                    "rounding": "half_up_to_six_decimal_places",
                                    "max_inventory_age_seconds": age_limit},
              "warnings": ["Scores are prototype operational priorities, not clinical triage or automatic dispatch authority.",
                           "Hard stock, batch, expiry and lane limits remain enforced. Routing feasibility must be checked separately.",
                           "Approval requires fresh score/stock checks and atomic resource reservations."]}
    if blocked:
        return result
    weights = {facility: int((Decimal(str(row["score"])) * PRIORITY_SCALE).to_integral_value(rounding=ROUND_HALF_UP))
               for facility, row in scored.items()}
    expiry = min([captured + timedelta(seconds=age_limit)] +
                 [utc_timestamp(row["valid_until"], "score.valid_until") for row in scored.values()])
    allocation = recommend_transport(transport, time_limit_seconds=time_limit_seconds,
                                     min_expiry_days=min_expiry_days, priority_weights=weights)
    result["allocation"] = allocation
    result["valid_until"] = expiry.isoformat()
    finished = utc_now() if now is None else current
    if finished >= expiry:
        result["status"] = "expired_during_computation"
    else:
        result["status"] = "recommended" if allocation["has_solution"] else "no_solution"
    return result
