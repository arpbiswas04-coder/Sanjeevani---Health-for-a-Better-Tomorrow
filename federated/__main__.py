import argparse
import json
import logging
import sys
from pathlib import Path

from federated.demo import run_demo
from optimization.common.validation import ValidationError


def main():
    parser = argparse.ArgumentParser(description="Three-region local federated learning mechanics demo")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--checkpoint", type=Path, help="Save after every round (path inside infra)")
    parser.add_argument("--resume", type=Path, help="Restore a checkpoint before additional rounds (path inside infra)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        infra_root = Path(__file__).resolve().parents[1]
        for path in (args.checkpoint, args.resume):
            if path is not None and not path.resolve().is_relative_to(infra_root):
                raise ValidationError("Checkpoint paths must stay inside infra")
        result = run_demo(args.rounds, resume_path=args.resume, checkpoint_path=args.checkpoint)
    except ValidationError as exc:
        print(json.dumps({"error": "invalid_request", "message": str(exc)}), file=sys.stderr)
        return 2
    except OSError:
        print(json.dumps({"error": "checkpoint_io_error", "message": "Unable to read or atomically save checkpoint"}), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
