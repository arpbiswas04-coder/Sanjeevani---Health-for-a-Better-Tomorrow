import copy
import hashlib
import json
import logging

from optimization.common.validation import ValidationError, identifier, integer, object_fields
from optimization.redistribution import recommend

LOGGER = logging.getLogger(__name__)
FIELDS = ("required_quantity", "fulfilled_quantity", "unresolved_shortage", "estimated_transport_cost_paise")


def _recommend(request, policy):
    result = recommend(request, policy)
    # These are simulation outputs, not actionable recommendation records.
    # Remove volatile identity/time fields to make replay comparisons exact.
    for field in ("recommendation_id", "generated_at"):
        result.pop(field)
    return result


def compare_scenarios(value):
    data = object_fields(value, required={"baseline", "scenarios"}, optional={"policy"}, path="simulation")
    scenarios = data["scenarios"]
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 50:
        raise ValidationError("Provide 1..50 scenarios")
    request = copy.deepcopy(data["baseline"])
    if not isinstance(request, dict) or not isinstance(request.get("candidate_sources"), list) or len(request["candidate_sources"]) > 1000:
        raise ValidationError("Baseline requires at most 1000 sources")
    policy = copy.deepcopy(data.get("policy", {}))
    baseline = _recommend(request, policy)
    results, seen = [], set()
    for raw in scenarios:
        scenario = object_fields(raw, required={"scenario_id"},
                                 optional={"required_quantity", "elapsed_days", "source_changes"}, path="scenario")
        scenario_id = identifier(scenario["scenario_id"], "scenario_id")
        if scenario_id in seen: raise ValidationError("Duplicate scenario ID")
        seen.add(scenario_id)
        snapshot = copy.deepcopy(request)
        days = integer(scenario.get("elapsed_days", 0), "elapsed_days")
        if days > 3650: raise ValidationError("Elapsed days exceeds simulation limit")
        snapshot["required_quantity"] = integer(scenario.get("required_quantity", request["required_quantity"]), "required_quantity")
        sources = {row["facility_id"]: row for row in snapshot["candidate_sources"]}
        for source in sources.values(): source["expiry_days"] -= days
        changes = scenario.get("source_changes", [])
        if not isinstance(changes, list) or len(changes) > len(sources):
            raise ValidationError("Invalid source changes")
        changed = set()
        for raw_change in changes:
            change = object_fields(raw_change, required={"facility_id"},
                optional={"unavailable", "lost_safe_surplus", "transport_cost_per_unit_paise"}, path="source change")
            node = identifier(change["facility_id"], "facility_id")
            if node not in sources or node in changed: raise ValidationError("Unknown or repeated source change")
            changed.add(node)
            source = sources[node]
            unavailable = change.get("unavailable", False)
            if type(unavailable) is not bool: raise ValidationError("unavailable must be boolean")
            loss = integer(change.get("lost_safe_surplus", 0), "lost_safe_surplus")
            if loss > source["safe_surplus"]: raise ValidationError("Lost surplus exceeds baseline safe surplus")
            source["safe_surplus"] = 0 if unavailable else source["safe_surplus"] - loss
            if "transport_cost_per_unit_paise" in change:
                source["transport_cost_per_unit_paise"] = integer(change["transport_cost_per_unit_paise"], "transport cost")
        result = _recommend(snapshot, policy)
        results.append({"scenario_id": scenario_id, "assumptions": copy.deepcopy(scenario),
                        "simulated_request": snapshot, "recommendation": result,
                        "delta_from_baseline": {field: result[field] - baseline[field] for field in FIELDS}})
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    LOGGER.info("simulation_completed scenarios=%d", len(results))
    return {"simulation_version": "redistribution-whatif-v1", "input_sha256": hashlib.sha256(encoded).hexdigest(),
            "simulation_only": True, "baseline": baseline, "scenarios": results,
            "limitations": ["Each scenario starts independently from the same snapshot; no live stock is changed.",
                            "Elapsed days only ages expiry; it does not forecast consumption or arrivals.",
                            "Single medicine/destination and one batch per source; linear transport cost model.",
                            "Lower cost can reflect unfulfilled demand; compare shortage and cost together.",
                            "No disease forecast, road network, dynamic digital twin or resilience score is modeled."]}
