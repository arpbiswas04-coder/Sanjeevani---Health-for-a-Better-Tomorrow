import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from optimization.ambulance import recommend_ambulance
from optimization.common.validation import ValidationError
from optimization.redistribution.cli import read_json


def main():
    parser = argparse.ArgumentParser(description="Read-only ambulance recommendation")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--demo", action="store_true", help="Use synthetic built-in candidates with current timestamps")
    parser.add_argument("--policy", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        request = read_json(Path(__file__).with_name("example.json") if args.demo else args.input)
        if args.demo:
            timestamp = datetime.now(timezone.utc).isoformat()
            request["captured_at"] = timestamp
            for candidate in request["candidates"]:
                candidate["observed_at"] = candidate["eta_observed_at"] = timestamp
        result = recommend_ambulance(request, read_json(args.policy) if args.policy else None)
    except (ValueError, OSError, UnicodeError) as exc:
        message = str(exc) if isinstance(exc, ValidationError) else "Unable to read valid request or policy JSON"
        print(json.dumps({"error": "invalid_request", "message": message}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
