"""Run a trusted transport request JSON from the command line."""

import argparse
import json
import logging
import sys
from pathlib import Path

from optimization.redistribution.cli import read_json
from optimization.transport import recommend_transport


def main():
    parser = argparse.ArgumentParser(description="Multi-destination medicine transport recommendation")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--time-limit", type=float, default=5)
    parser.add_argument("--min-expiry-days", type=int, default=1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        result = recommend_transport(read_json(args.input), time_limit_seconds=args.time_limit,
                                     min_expiry_days=args.min_expiry_days)
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({"error": "invalid_request", "message": str(exc)}), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(json.dumps({"error": "solver_error", "message": str(exc)}), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["has_solution"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
