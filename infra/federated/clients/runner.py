"""Bounded round polling. Ambiguous submission failures are never retried."""
import time
from federated.strategies.fedavg import MODEL_SCHEMA, parameters
from optimization.common.validation import ValidationError, integer, object_fields


def _state(value):
    state = object_fields(value, required={"challenge", "round", "model_version", "model_schema", "parameters"}, optional=set(), path="round response")
    challenge = state["challenge"]
    if not isinstance(challenge, str) or len(challenge) != 64 or any(c not in "0123456789abcdef" for c in challenge):
        raise ValidationError("Invalid round challenge")
    integer(state["round"], "round", 1)
    integer(state["model_version"], "model_version")
    if state["model_schema"] != MODEL_SCHEMA: raise ValidationError("Unsupported model schema")
    parameters(state["parameters"])
    return state


def run_rounds(client, train, signing_key, *, rounds=1, poll_seconds=15, max_wait_seconds=600,
               clock=time.monotonic, sleep=time.sleep):
    count = integer(rounds, "rounds", 1)
    poll = integer(poll_seconds, "poll_seconds", 5)
    timeout = integer(max_wait_seconds, "max_wait_seconds", 1)
    if count > 100 or poll > 300 or timeout > 86400:
        raise ValidationError("Runner limits exceeded")
    deadline = clock() + timeout
    accepted, seen = [], set()
    stale_training = 0
    while len(accepted) < count and clock() < deadline:
        state = _state(client.round_request())
        challenge = state["challenge"]
        if challenge not in seen and clock() < deadline:
            update = train(state)
            if clock() >= deadline: break
            current = _state(client.round_request())
            if current != state:
                stale_training += 1
            else:
                # A round can still close after this check. Fail rather than retry
                # a rejected or ambiguously acknowledged update automatically.
                reply = client.submit(update, challenge, signing_key)
                if not isinstance(reply, dict) or reply.get("status") != "pending" or reply.get("node_id") != update.get("node_id") or reply.get("round") != state["round"]:
                    raise ValidationError("Invalid submission acknowledgement")
                seen.add(challenge)
                accepted.append({"node_id": reply["node_id"], "round": state["round"], "model_version": state["model_version"], "status": "pending"})
        if len(accepted) < count:
            remaining = deadline - clock()
            if remaining > 0: sleep(min(poll, remaining))
    return {"status": "submitted" if len(accepted) == count else "timeout", "requested_rounds": count,
            "accepted_submissions": accepted, "discarded_stale_training": stale_training,
            "aggregation_confirmed": False}
