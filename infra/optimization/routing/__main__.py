import argparse
import json
import logging
import sys
from pathlib import Path

from optimization.common.validation import ValidationError
from optimization.redistribution.cli import read_json
from optimization.routing import recommend_routes


def main():
    parser = argparse.ArgumentParser(description="Vehicle delivery route recommendations")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=3)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        result = recommend_routes(read_json(args.input), time_limit_seconds=args.time_limit)
    except (ValueError, OSError, UnicodeError) as exc:
        message = str(exc) if isinstance(exc, ValidationError) else "Unable to read valid routing JSON"
        print(json.dumps({"error": "invalid_request", "message": message}), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(json.dumps({"error": "solver_error", "message": str(exc)}), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["has_solution"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
