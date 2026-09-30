# Signed federation update admission

`federated/server/admission.py` adds an opt-in authentication boundary around the
existing coordinator. Each node uses a different random secret of at least 32
bytes. HMAC-SHA256 signs the complete update, protocol version, server challenge
and issue timestamp. The receiver binds the verified key to the claimed node ID
before accepting its contribution.

The boundary checks model version, round, schema and update values, permits one
contribution per node per round, and rejects packets older than 120 seconds or
more than 30 seconds in the future. Server clocks must be synchronized. A fresh
random challenge on startup and after each closed round invalidates old packets,
including after checkpoint recovery. Signature verification uses constant-time
comparison. Packets are limited to 16 KiB and duplicate JSON keys are rejected.

## Integration sequence

1. Provision distinct random node keys through a secret manager. A node receives
   only its own key; the coordinator needs all authorized keys. No credentials
   are generated, written to disk or committed by this change.
2. Construct `AuthenticatedRounds(coordinator, node_keys)` with byte-valued keys.
   It clones the coordinator and owns all subsequent model mutations.
3. Send `round_request()` to a node through server-authenticated HTTPS. It returns
   parameters, schema, round, model version and the current challenge.
4. Train locally. Pass the existing update dictionary, challenge and node key to
   `sign_update(update, challenge, key)`; it returns JSON bytes.
5. The service passes those bytes to `submit(raw)`. A successful response means
   the update is pending, not yet aggregated. Invalid submissions raise
   `ValidationError` without consuming the node's slot or altering the model.
6. At the round deadline or selected quorum, an operator/controller invokes
   `close_round()`. Participants must never be given this administrative operation.
   The existing minimum-participant policy decides whether aggregation occurs.
7. Call `save(path)` between rounds. Recover with `load_checkpoint(path)` and
   construct a new admission instance using separately supplied keys.

Example of server construction (the secrets here are ephemeral demonstration
values; real nodes need separately provisioned persistent keys):

```python
import secrets
from federated.server.coordinator import Coordinator
from federated.server.admission import AuthenticatedRounds

nodes = {"district-a": "region-a", "district-b": "region-b"}
keys = {node: secrets.token_bytes(32) for node in nodes}
server = AuthenticatedRounds(Coordinator(nodes), keys)
request = server.round_request()
```

## Operational limits

This is a library boundary. A separate [mutual-TLS development service](federated-https.md)
now uses it for HTTPS requests; no deployment has been performed. The existing local
and subprocess demos continue to use their original unauthenticated coordinator;
they do not automatically gain protection from this module. The HTTPS service adds
certificate verification, endpoint identity checks and body limits before buffering.
Rate limits and secret-manager integration remain to be built.

HMAC does not encrypt parameters. The coordinator also possesses signing keys;
this is not non-repudiation. Authorized malicious nodes can still submit poisoned
updates. Secure aggregation and differential privacy are separate pending work.

Pending updates live in memory and are lost on restart. Clients must fetch a
fresh challenge and resubmit. A duplicate submission raises an error, so clients
must not assume a lost acknowledgement means rejection. Closing a round with
insufficient participants still advances the round; no automatic scheduler is
provided. Checkpoints contain neither keys nor challenges and retain their
existing [integrity and durability limits](federated-checkpoints.md).

To revoke/rotate a key, stop admission, close or discard the pending round,
save completed state if needed, then create a new instance with the replacement
key set. This invalidates all outstanding challenges. There is no hot rotation.

Three focused checks cover valid aggregation, replay, impersonation, tampering,
timestamp/version rejection, restart invalidation and malformed/oversized JSON:

```powershell
# From infra/
.\.venv\Scripts\python.exe -m unittest federated.tests.test_admission -v
```

No external dependencies or training jobs are required for these checks.
