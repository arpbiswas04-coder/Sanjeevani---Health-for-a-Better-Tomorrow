"""Transparent operational scenario scoring; recommendations only, not clinical risk."""
import argparse
import json
import math
from pathlib import Path
from optimization.common.validation import ValidationError, identifier, nonnegative_number, object_fields
from optimization.simulation.comparison import compare_timelines


from optimization.common.telemetry import measured


@measured("optimizer", "resilience")
def assess_resilience(comparison, policy):
    policy = object_fields(policy, required={"version", "scenario_weights"}, optional=set(), path="resilience policy")
    version = identifier(policy["version"], "policy version")
    result = compare_timelines(comparison)
    weights = policy["scenario_weights"]
    if not isinstance(weights, dict) or set(weights) != {row["scenario_id"] for row in result["scenarios"]}:
        raise ValidationError("Weights must exactly cover the compared scenarios")
    weights = {name: nonnegative_number(value, "scenario weight") for name, value in weights.items()}
    total = sum(weights.values())
    if not math.isfinite(total) or total <= 0: raise ValidationError("Positive finite total weight required")
    rows = []
    for scenario in result["scenarios"]:
        fraction = scenario["summary"]["fulfillment_fraction"]
        rows.append({"scenario_id": scenario["scenario_id"], "weight": weights[scenario["scenario_id"]] / total,
                     "fulfillment_fraction": fraction, "unmet_demand": scenario["summary"]["unmet_demand"],
                     "delta_from_baseline": scenario["delta_from_baseline"]["fulfillment_fraction"]})
    score = None if any(row["weight"] > 0 and row["fulfillment_fraction"] is None for row in rows) else sum(
        100 * row["weight"] * (row["fulfillment_fraction"] or 0) for row in rows)
    return {"version": "operational-resilience-v1", "policy_version": version, "simulation_only": True,
            "recommendation_only": True, "input_sha256": result["input_sha256"], "score_0_to_100": score,
            "status": "unscored_zero_demand" if score is None else "scored", "scenarios": rows,
            "definition": "100 times scenario-weighted transfer-demand fulfillment; weights are planning priorities, not probabilities or clinical validation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON with comparison and policy")
    args = parser.parse_args()
    try:
        data = object_fields(json.loads(args.input.read_text()), required={"comparison", "policy"}, optional=set(), path="input")
        print(json.dumps(assess_resilience(**data), indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError):
        print(json.dumps({"error": "invalid_resilience_input"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
