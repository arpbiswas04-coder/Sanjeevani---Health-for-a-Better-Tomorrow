import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path

from optimization.common.validation import ValidationError
from optimization.redistribution.cli import read_json
from optimization.workforce import recommend_staff


def main():
    parser = argparse.ArgumentParser(description="Single-shift staff redistribution recommendations")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--demo", action="store_true", help="Use synthetic roster with refreshed times")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        request = json.loads(files("optimization.workforce").joinpath("example.json").read_text(encoding="utf-8")) if args.demo else read_json(args.input)
        if args.demo:
            current = datetime.now(timezone.utc)
            request["captured_at"] = current.isoformat()
            request["shift_start"] = (current + timedelta(hours=1)).isoformat()
            request["shift_end"] = (current + timedelta(hours=9)).isoformat()
            for worker in request["workers"]:
                worker["observed_at"] = worker["available_from"] = current.isoformat()
                worker["available_until"] = (current + timedelta(hours=11)).isoformat()
        result = recommend_staff(request)
    except (ValueError, OSError, UnicodeError) as exc:
        message = str(exc) if isinstance(exc, ValidationError) else "Unable to read valid workforce JSON"
        print(json.dumps({"error": "invalid_request", "message": message}), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(json.dumps({"error": "solver_error", "message": str(exc)}), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["status"] == "recommended" else 4


if __name__ == "__main__":
    raise SystemExit(main())
