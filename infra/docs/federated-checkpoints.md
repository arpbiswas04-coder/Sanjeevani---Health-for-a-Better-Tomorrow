# Federated checkpoint saving and recovery

Implemented in `federated/server/checkpoints.py`, using only the standard library.
Checkpoints contain global parameters, model schema/version, next round,
minimum-participant setting, node registry and last accepted metadata. They do
not contain raw client samples or individual model updates.

## Save and resume from infra/

```powershell
.\.venv\Scripts\python.exe -m federated --rounds 2 --checkpoint federated/checkpoints/demo.json
.\.venv\Scripts\python.exe -m federated --rounds 3 --resume federated/checkpoints/demo.json --checkpoint federated/checkpoints/demo.json
```

The second command runs three additional rounds, ending at model version 5 if
all rounds aggregate. Saving occurs after every processed round. `--resume`
alone loads but does not save; add `--checkpoint` for continued persistence.
Both CLI paths must stay inside `infra/`. The conventional checkpoint directory
is gitignored. Default demo execution still writes nothing.

```python
from federated.server.checkpoints import load_checkpoint, save_checkpoint

save_checkpoint(coordinator, "federated/checkpoints/current.json")
restored = load_checkpoint("federated/checkpoints/current.json")
```

Library callers explicitly choose the path; the CLI adds the infra-only path
restriction. Restore returns a new coordinator rather than changing a running
one. The demo additionally requires the restored node registry and minimum
participation to match its config. Client data remains client-owned and must be
recreated/reloaded separately.

## Integrity and write behavior

Format version 1 uses a JSON payload with saved time and a SHA-256 checksum of
canonical JSON. Reads are limited to 1 MiB and reject duplicate keys, malformed
JSON, non-finite values, unsupported schemas, inconsistent round/version metadata
and invalid node observations. Only fully validated state is constructed.

The writer validates state, writes a temporary file in the target directory,
flushes and fsyncs it, then atomically replaces the target. If replacement fails,
the previous target survives and the temporary file is cleaned up on a handled
failure. Existing corrupt or unrelated files are refused rather than overwritten;
choose a new path or recover from a separate known-good checkpoint.

One writer owns each path and saving occurs between rounds. There is no lock,
concurrent-writer coordination, history retention, remote backup or transaction
coupling between in-memory training and disk writes. If saving fails, the CLI
stops; the current process may already have advanced past the last persisted
round. Recovery resumes from the last successful save.

Atomic replacement protects against partial target files on supported local
filesystems; directory-entry durability through sudden power loss is not
guaranteed on every platform/filesystem. A process crash can leave a temporary
file, which is never automatically loaded. No pickle or executable payload is
used. The checksum detects accidental corruption, **not malicious tampering**:
someone able to rewrite both payload and checksum can alter valid-looking state.
Access controls, authenticity, encryption and rollback protection remain pending.

## Verification

Six targeted checks passed: exact state roundtrip, recovery after insufficient
participation, resumed versus uninterrupted training, corruption/state rejection,
simulated atomic-replace failure preserving the prior checkpoint, and invalid/
oversized/unrelated file handling. Temporary test files stayed inside `infra/`
and were cleaned up. No long-running service or broad suite was run.

CLI exit 2 reports invalid checkpoint/configuration; exit 3 reports filesystem
read/write failure. Next: Flower/PyTorch adapters and regional process execution,
followed by authenticated transport and privacy mechanisms.
