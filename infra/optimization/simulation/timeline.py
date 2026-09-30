"""Sequential safe-surplus ledger, without live transfers or replenishment."""
import copy
import hashlib
import json
import logging

from optimization.common.validation import ValidationError, identifier, integer, object_fields
from optimization.simulation.engine import _recommend


def run_timeline(value):
    data = object_fields(value, required={"baseline", "periods"}, optional={"policy"}, path="timeline")
    baseline = copy.deepcopy(data["baseline"])
    if not isinstance(baseline, dict) or not isinstance(baseline.get("candidate_sources"), list) or len(baseline["candidate_sources"]) > 1000:
        raise ValidationError("Baseline requires at most 1000 sources")
    policy = copy.deepcopy(data.get("policy", {}))
    _recommend(baseline, policy)  # Validate the entire initial snapshot before simulation.
    periods = data["periods"]
    if not isinstance(periods, list) or not 1 <= len(periods) <= 365:
        raise ValidationError("Provide 1..365 periods")
    remaining = {row["facility_id"]: row["safe_surplus"] for row in baseline["candidate_sources"]}
    initial = sum(remaining.values())
    rows = []
    totals = {"delivered": 0, "lost": 0, "expired": 0, "unmet_demand": 0, "transport_cost_paise": 0}
    previous = -1
    for raw in periods:
        period = object_fields(raw, required={"day", "demand"}, optional={"blocked_sources", "losses"}, path="period")
        day = integer(period["day"], "day")
        if day <= previous or day > 3650: raise ValidationError("Days must increase strictly within 0..3650")
        previous = day
        demand = integer(period["demand"], "demand")
        blocked = period.get("blocked_sources", [])
        if not isinstance(blocked, list): raise ValidationError("blocked_sources must be an array")
        blocked = [identifier(node, "blocked source") for node in blocked]
        if len(blocked) != len(set(blocked)) or not set(blocked) <= remaining.keys():
            raise ValidationError("Unknown or duplicate blocked source")
        opening = dict(remaining)
        expired, losses = {}, {}
        # Expiry removes stock at the start of the day, before explicit losses.
        for source in baseline["candidate_sources"]:
            node = source["facility_id"]
            if source["expiry_days"] - day <= 0 and remaining[node]:
                expired[node] = remaining[node]
                remaining[node] = 0
        changes = period.get("losses", [])
        if not isinstance(changes, list) or len(changes) > len(remaining):
            raise ValidationError("Invalid losses")
        for raw_loss in changes:
            loss = object_fields(raw_loss, required={"facility_id", "quantity"}, optional=set(), path="loss")
            node = identifier(loss["facility_id"], "loss facility")
            amount = integer(loss["quantity"], "loss quantity")
            if node not in remaining or node in losses or amount > remaining[node]:
                raise ValidationError("Unknown/duplicate loss or loss exceeds remaining unexpired surplus")
            losses[node] = amount
            remaining[node] -= amount
        request = copy.deepcopy(baseline)
        request["required_quantity"] = demand
        for source in request["candidate_sources"]:
            node = source["facility_id"]
            source["expiry_days"] -= day
            source["safe_surplus"] = 0 if node in blocked else remaining[node]
        recommendation = _recommend(request, policy)
        delivered = {node: 0 for node in remaining}
        for transfer in recommendation["recommended_transfers"]:
            node, amount = transfer["source"], transfer["quantity"]
            remaining[node] -= amount
            delivered[node] += amount
        for node in remaining:
            if remaining[node] < 0 or opening[node] != remaining[node] + delivered[node] + losses.get(node, 0) + expired.get(node, 0):
                raise RuntimeError("Simulation stock conservation failed")
        totals["delivered"] += recommendation["fulfilled_quantity"]
        totals["unmet_demand"] += recommendation["unresolved_shortage"]
        totals["transport_cost_paise"] += recommendation["estimated_transport_cost_paise"]
        totals["lost"] += sum(losses.values())
        totals["expired"] += sum(expired.values())
        rows.append({"day": day, "assumptions": copy.deepcopy(period), "opening_safe_surplus": opening,
                     "expired": expired, "losses": losses, "simulated_deliveries": delivered,
                     "closing_safe_surplus": dict(remaining), "recommendation": recommendation})
    logging.getLogger(__name__).info("timeline_completed periods=%d", len(rows))
    return {"simulation_version": "safe-surplus-timeline-v1", "simulation_only": True,
            "input_sha256": hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
            "periods": rows, "totals": totals, "initial_safe_surplus": initial,
            "final_safe_surplus": remaining,
            "assumptions": ["Hypothetical immediate deliveries are consumed within each period; no real approval or dispatch occurs.",
                            "Demand is externally supplied and unmet demand is not carried forward.",
                            "Only transferable safe surplus is tracked; protected stock and source consumption are outside this ledger.",
                            "No replenishment, destination storage, travel delays, forecasting or resilience score.",
                            "Blocked access lasts one period and does not destroy stock. Expiry occurs before explicit losses.",
                            "Days are offsets from the initial snapshot; unlisted days have no demand or delivery events."]}
