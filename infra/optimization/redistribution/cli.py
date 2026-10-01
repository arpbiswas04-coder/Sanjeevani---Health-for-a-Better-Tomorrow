"""JSON command-line interface. Results go to stdout; diagnostics to stderr."""

import argparse
import json
import logging
import sys
from pathlib import Path

from optimization.common.validation import ValidationError
from optimization.redistribution import recommend


def read_json(path: Path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError("JSON contains duplicate object keys")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValidationError("JSON contains a non-finite numeric constant")

    return json.loads(
        path.read_text(encoding="utf-8-sig"),
        object_pairs_hook=unique_keys,
        parse_constant=reject_constant,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Recommend medicine transfers from a JSON inventory snapshot")
    parser.add_argument("--input", type=Path, help="Path to the request JSON")
    parser.add_argument("--policy", type=Path, help="Optional policy JSON")
    parser.add_argument("--healthcheck", action="store_true", help="Check module execution; does not check external services")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    if args.healthcheck:
        print(json.dumps({"status": "ok", "component": "redistribution", "version": "0.1.0"}))
        return 0
    if args.input is None:
        parser.error("--input is required unless --healthcheck is used")
    try:
        request = read_json(args.input)
        policy = read_json(args.policy) if args.policy else None
        result = recommend(request, policy)
    except (ValidationError, ValueError, OSError, UnicodeError, RecursionError) as exc:
        # Do not echo raw input, inventory data, paths, or secrets in diagnostics.
        message = str(exc) if isinstance(exc, ValidationError) else "Unable to read valid JSON input or policy"
        print(json.dumps({"error": "invalid_request", "message": message}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

