"""Bounded JSON checkpoints with integrity checking and atomic replacement.

The checksum detects accidental corruption, not malicious editing. No pickle,
raw client samples, individual updates or executable objects are serialized.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile

from federated.server.coordinator import Coordinator
from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, object_fields

MAX_BYTES = 1_048_576


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def save_checkpoint(coordinator, path):
    """Save one coordinator snapshot. One writer per path is required.

    Existing valid checkpoints may be replaced; unrelated/corrupt files are
    refused. Restore happens between rounds; no concurrent coordinator mutation.
    """
    target = Path(path)
    state = coordinator.state()
    Coordinator.from_state(state)
    payload = {"checkpoint_version": 1, "saved_at": utc_now().isoformat(), "state": state}
    envelope = {"payload": payload, "sha256": hashlib.sha256(_canonical(payload)).hexdigest()}
    encoded = _canonical(envelope)
    if len(encoded) > MAX_BYTES: raise ValidationError("Checkpoint exceeds size limit")
    if target.exists(): load_checkpoint(target)  # Never overwrite an unrelated file.
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".checkpoint-", suffix=".tmp", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"path": str(target), "model_version": state["model_version"], "next_round": state["next_round"]}


def load_checkpoint(path):
    """Read and validate a checkpoint without mutating an existing coordinator."""
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES: raise ValidationError("Checkpoint exceeds size limit")
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValidationError("Checkpoint contains duplicate JSON keys")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValidationError("Checkpoint contains a non-finite number")
    try:
        envelope = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys, parse_constant=reject_constant)
        document = object_fields(envelope, required={"payload", "sha256"}, optional=set(), path="checkpoint")
        payload = object_fields(document["payload"], required={"checkpoint_version", "saved_at", "state"}, optional=set(), path="payload")
        if type(payload["checkpoint_version"]) is not int or payload["checkpoint_version"] != 1:
            raise ValidationError("Unsupported checkpoint format version")
        utc_timestamp(payload["saved_at"], "saved_at")
        checksum = document["sha256"]
        if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            raise ValidationError("Invalid checkpoint checksum format")
        if not hmac.compare_digest(checksum, hashlib.sha256(_canonical(payload)).hexdigest()):
            raise ValidationError("Checkpoint integrity check failed")
        return Coordinator.from_state(payload["state"])
    except (ValueError, UnicodeError, RecursionError, TypeError, OverflowError) as exc:
        if isinstance(exc, ValidationError): raise
        raise ValidationError("Malformed checkpoint JSON or state") from exc
