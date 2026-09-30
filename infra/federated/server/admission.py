"""Authenticated update admission, independent of the future HTTPS transport.

HMAC authenticates possession of a shared node secret; it does not encrypt
updates or defend against a compromised authorized node/coordinator.
"""

import hashlib
import hmac
import json
import secrets
import threading
import time

from federated.server.coordinator import Coordinator
from federated.strategies.fedavg import validate_update
from optimization.common.validation import ValidationError, integer, object_fields

MAX_PACKET_BYTES = 16384
DOMAIN = b"sanjeevani-federation-update-v1\x00"


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _key(key):
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValidationError("Node keys require at least 32 random bytes")
    return key


def sign_update(update, challenge, key, *, now=None):
    """Sign the complete update and the server's current challenge.

    Fetch challenges using server-authenticated TLS when adding a network
    transport. Provision each client with only its own key.
    """
    issued = integer(int(time.time()) if now is None else now, "issued_at")
    payload = {"protocol": 1, "challenge": challenge, "issued_at": issued, "update": update}
    signature = hmac.new(_key(key), DOMAIN + _encode(payload), hashlib.sha256).hexdigest()
    raw = _encode({"payload": payload, "signature": signature})
    if len(raw) > MAX_PACKET_BYTES:
        raise ValidationError("Signed update exceeds size limit")
    return raw


def _decode(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_PACKET_BYTES:
        raise ValidationError("Invalid signed update size/type")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValidationError("Duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise ValidationError("Non-finite JSON number")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Malformed signed update") from exc


class AuthenticatedRounds:
    """Own coordinator mutations and serialize admission/round closing.

    Clone the supplied coordinator to prevent outside mutation. Pending updates
    are memory-only. New random challenges on startup and after every close
    invalidate old packets even when recovering an earlier checkpoint.
    """

    def __init__(self, coordinator, node_keys):
        self._coordinator = Coordinator.from_state(coordinator.state())
        if set(node_keys) != set(self._coordinator.state()["nodes"]):
            raise ValidationError("Provide exactly one key per registered node")
        self._keys = {node: _key(key) for node, key in node_keys.items()}
        if len(set(self._keys.values())) != len(self._keys):
            raise ValidationError("Nodes must have distinct keys")
        self._lock = threading.Lock()
        self._pending = {}
        self._challenge = secrets.token_hex(32)

    def state(self):
        with self._lock:
            return self._coordinator.state()

    def round_request(self):
        with self._lock:
            state = self._coordinator.state()
            return {"challenge": self._challenge, "round": state["next_round"],
                    "model_version": state["model_version"], "model_schema": state["model_schema"],
                    "parameters": state["parameters"]}

    def submit(self, raw, *, now=None, expected_node=None):
        """Reject invalid/replayed packets without modifying pending/model state."""
        packet = object_fields(_decode(raw), required={"payload", "signature"}, optional=set(), path="packet")
        payload = object_fields(packet["payload"], required={"protocol", "challenge", "issued_at", "update"},
                                optional=set(), path="payload")
        with self._lock:
            update = payload["update"]
            node = update.get("node_id") if isinstance(update, dict) else None
            if expected_node is not None and node != expected_node:
                raise ValidationError("Certificate and update identity differ")
            if not isinstance(node, str) or node not in self._keys:
                raise ValidationError("Update authentication failed")
            signature = packet["signature"]
            if not isinstance(signature, str) or len(signature) != 64 or any(c not in "0123456789abcdef" for c in signature):
                raise ValidationError("Update authentication failed")
            try:
                expected = hmac.new(self._keys[node], DOMAIN + _encode(payload), hashlib.sha256).hexdigest()
            except (ValueError, TypeError, RecursionError) as exc:
                raise ValidationError("Malformed signed payload") from exc
            if not hmac.compare_digest(signature, expected):
                raise ValidationError("Update authentication failed")
            if type(payload["protocol"]) is not int or payload["protocol"] != 1 or payload["challenge"] != self._challenge:
                raise ValidationError("Unsupported protocol or expired round challenge")
            issued = integer(payload["issued_at"], "issued_at")
            current = integer(int(time.time()) if now is None else now, "now")
            if not current - 120 <= issued <= current + 30:
                raise ValidationError("Update timestamp outside allowed window")
            state = self._coordinator.state()
            validated = validate_update(update, expected_round=state["next_round"], expected_version=state["model_version"])
            if node in self._pending:
                raise ValidationError("Node already submitted this round")
            self._pending[node] = validated
            return {"node_id": node, "status": "pending", "round": state["next_round"]}

    def close_round(self):
        """Operator-only boundary; never expose as a participant endpoint.

        A close with insufficient participants still advances the round using
        existing coordinator semantics. Call at the chosen deadline or quorum.
        """
        with self._lock:
            result = self._coordinator.aggregate_round(list(self._pending.values()))
            self._pending.clear()
            self._challenge = secrets.token_hex(32)
            return result

    def save(self, path):
        """Checkpoint only between rounds; secrets/challenges are never saved."""
        from federated.server.checkpoints import save_checkpoint
        with self._lock:
            if self._pending: raise ValidationError("Close the pending round before checkpointing")
            return save_checkpoint(self._coordinator, path)
