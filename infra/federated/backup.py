"""Encrypted federation state backups; restores always create a new checkpoint."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from federated.server.checkpoints import load_checkpoint, save_checkpoint
from federated.server.coordinator import Coordinator
from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, object_fields

ROOT = Path(__file__).resolve().parents[1]
MAX_BACKUP = 2_097_152


def _target(path):
    target = Path(path).absolute()
    if not target.resolve().is_relative_to(ROOT):
        raise ValidationError("Output must stay inside infra")
    if target.exists() or target.is_symlink():
        raise FileExistsError("Existing output will not be replaced")
    return target


def _publish(staged, target):
    # Atomic exclusive publication: never replace an existing file, even in a race.
    # Both paths are on the same filesystem. Unsupported hard links fail safely.
    os.link(staged, target)


def backup(source, destination, key):
    from cryptography.fernet import Fernet
    target = _target(destination)
    coordinator = load_checkpoint(source)
    payload = {"backup_version": 1, "created_at": utc_now().isoformat(), "state": coordinator.state()}
    token = Fernet(key).encrypt(json.dumps(payload, allow_nan=False, separators=(",", ":")).encode())
    if len(token) > MAX_BACKUP: raise ValidationError("Backup exceeds size limit")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".backup-", dir=target.parent) as folder:
        staged = Path(folder) / "encrypted"
        with staged.open("xb") as stream:
            stream.write(token)
            stream.flush()
            os.fsync(stream.fileno())
        _publish(staged, target)
    return {"status": "backed_up", "path": str(target), "model_version": payload["state"]["model_version"]}


def inspect_backup(source, key):
    from cryptography.fernet import Fernet, InvalidToken
    with Path(source).open("rb") as stream:
        raw = stream.read(MAX_BACKUP + 1)
    if len(raw) > MAX_BACKUP: raise ValidationError("Backup exceeds size limit")
    def pairs(items):
        row = {}
        for name, value in items:
            if name in row: raise ValidationError("Duplicate backup field")
            row[name] = value
        return row
    def constant(value):
        raise ValidationError("Non-finite backup number")
    try:
        value = json.loads(Fernet(key).decrypt(raw), object_pairs_hook=pairs, parse_constant=constant)
        payload = object_fields(value, required={"backup_version", "created_at", "state"}, optional=set(), path="backup")
        if type(payload["backup_version"]) is not int or payload["backup_version"] != 1:
            raise ValidationError("Unsupported backup version")
        utc_timestamp(payload["created_at"], "created_at")
        return Coordinator.from_state(payload["state"]), payload["created_at"]
    except (InvalidToken, ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ValidationError("Backup authentication or validation failed") from exc


def restore(source, destination, key):
    target = _target(destination)
    coordinator, created_at = inspect_backup(source, key)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".restore-", dir=target.parent) as folder:
        staged = Path(folder) / "checkpoint.json"
        save_checkpoint(coordinator, staged)
        if load_checkpoint(staged).state() != coordinator.state():
            raise ValidationError("Restored checkpoint verification failed")
        _publish(staged, target)
    return {"status": "restored", "path": str(target), "backup_created_at": created_at,
            "model_version": coordinator.state()["model_version"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "verify", "restore"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--key-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.key_file.open("rb") as stream:
            key = stream.read(129).strip()
        if len(key) != 44: raise ValidationError("Expected a generated Fernet key")
        if args.action == "verify":
            if args.output is not None: raise ValidationError("Verify has no output file")
            coordinator, created_at = inspect_backup(args.source, key)
            result = {"status": "verified", "backup_created_at": created_at,
                      "model_version": coordinator.state()["model_version"]}
        else:
            if args.output is None: raise ValidationError("Output is required")
            result = (backup if args.action == "backup" else restore)(args.source, args.output, key)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, ImportError):
        print("federation_backup_failed: check key, input integrity, output path and filesystem support")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
