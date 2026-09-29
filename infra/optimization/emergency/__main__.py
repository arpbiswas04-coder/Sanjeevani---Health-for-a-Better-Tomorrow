import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

from optimization.common.validation import ValidationError
from optimization.emergency import score_emergency_priorities
from optimization.redistribution.cli import read_json


def main():
    parser = argparse.ArgumentParser(description="Explainable operational facility priority scores")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--demo", action="store_true", help="Evaluate synthetic inputs with refreshed timestamps")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--resources", action="store_true", help="Combine scoring with constrained transport allocation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        example = "resource-example.json" if args.resources else "example.json"
        request = json.loads(files("optimization.emergency").joinpath(example).read_text(encoding="utf-8")) if args.demo else read_json(args.input)
        if args.demo:
            stamp = datetime.now(timezone.utc).isoformat()
            risk = request["risk_request"] if args.resources else request
            if args.resources: request["inventory_captured_at"] = stamp
            risk["captured_at"] = stamp
            for facility in risk["facilities"]:
                for signal in facility["signals"].values():
                    if signal is not None: signal["observed_at"] = stamp
        policy = read_json(args.policy) if args.policy else None
        if args.resources:
            from optimization.emergency.resources import recommend_emergency_resources
            result = recommend_emergency_resources(request, policy)
        else:
            result = score_emergency_priorities(request, policy)
    except (ValueError, OSError, UnicodeError) as exc:
        message = str(exc) if isinstance(exc, ValidationError) else "Unable to read valid input or policy JSON"
        print(json.dumps({"error": "invalid_request", "message": message}), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(json.dumps({"error": "solver_error", "message": str(exc)}), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, allow_nan=False))
    return 4 if args.resources and result["status"] != "recommended" else 0


if __name__ == "__main__":
    raise SystemExit(main())
