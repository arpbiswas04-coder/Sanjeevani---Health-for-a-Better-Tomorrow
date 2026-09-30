import argparse
import json
from pathlib import Path
import sys

from optimization.simulation import compare_scenarios
from optimization.simulation.timeline import run_timeline


def main():
    parser = argparse.ArgumentParser(description="Compare isolated redistribution what-if scenarios")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--timeline", action="store_true", help="Simulate consecutive periods instead of independent scenarios")
    args = parser.parse_args()
    if bool(args.input) == args.demo: parser.error("Choose exactly one of --input or --demo")
    try:
        path = Path(__file__).with_name("timeline-example.json" if args.timeline else "example.json") if args.demo else args.input
        with path.open("rb") as stream: raw = stream.read(1_048_577)
        if len(raw) > 1_048_576: raise ValueError("Input exceeds 1 MiB")
        result = (run_timeline if args.timeline else compare_scenarios)(json.loads(raw))
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        print(json.dumps({"error": "simulation_failed", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
