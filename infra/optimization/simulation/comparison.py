"""Compare sequential scenarios on a shared initial snapshot and day grid."""
import copy
import hashlib
import json

from optimization.common.validation import ValidationError, identifier, object_fields
from optimization.simulation.timeline import run_timeline


def _summary(result):
    totals = result["totals"]
    demand = totals["delivered"] + totals["unmet_demand"]
    return {**totals, "demand": demand,
            "fulfillment_fraction": totals["delivered"] / demand if demand else None,
            "periods_with_shortage": sum(row["recommendation"]["unresolved_shortage"] > 0 for row in result["periods"]),
            "ending_safe_surplus": sum(result["final_safe_surplus"].values())}


def compare_timelines(value):
    data = object_fields(value, required={"baseline", "baseline_periods", "scenarios"}, optional={"policy"}, path="comparison")
    variants = data["scenarios"]
    if not isinstance(variants, list) or not 1 <= len(variants) <= 10:
        raise ValidationError("Provide 1..10 timeline scenarios")
    base_input = {"baseline": copy.deepcopy(data["baseline"]), "periods": copy.deepcopy(data["baseline_periods"]),
                  "policy": copy.deepcopy(data.get("policy", {}))}
    base = run_timeline(base_input)
    summary = _summary(base)
    days = [period["day"] for period in base["periods"]]
    seen, comparisons = set(), []
    for raw in variants:
        scenario = object_fields(raw, required={"scenario_id", "periods"}, optional=set(), path="scenario")
        name = identifier(scenario["scenario_id"], "scenario_id")
        if name in seen: raise ValidationError("Duplicate scenario ID")
        seen.add(name)
        periods = scenario["periods"]
        if not isinstance(periods, list) or any(not isinstance(row, dict) for row in periods):
            raise ValidationError("Scenario periods must be objects")
        if [row.get("day") for row in periods] != days:
            raise ValidationError("Scenarios must use the same ordered days as baseline_periods")
        result = run_timeline({**base_input, "periods": copy.deepcopy(periods)})
        metrics = _summary(result)
        delta = {key: (metrics[key] - summary[key] if metrics[key] is not None and summary[key] is not None else None)
                 for key in summary}
        per_day = [{"day": current["day"],
                    "unmet_demand_delta": current["recommendation"]["unresolved_shortage"] - original["recommendation"]["unresolved_shortage"],
                    "delivered_delta": current["recommendation"]["fulfilled_quantity"] - original["recommendation"]["fulfilled_quantity"]}
                   for original, current in zip(base["periods"], result["periods"])]
        comparisons.append({"scenario_id": name, "summary": metrics, "delta_from_baseline": delta,
                            "per_day_deltas": per_day, "timeline": result})
    return {"simulation_version": "timeline-comparison-v1", "simulation_only": True,
            "input_sha256": hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
            "baseline": {"summary": summary, "timeline": base}, "scenarios": comparisons,
            "interpretation": ["Deltas are scenario minus baseline; positive unmet demand means more shortage.",
                               "Fulfillment fractions are null when demand is zero; differences are fraction points, not percent change.",
                               "Compare demand, shortage and cost together; lower cost may mean fewer deliveries.",
                               "Shared snapshot, policy and days improve comparability but do not establish causation or clinical benefit.",
                               "No automatic scenario ranking or resilience score is assigned."]}
