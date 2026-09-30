# Federated learning foundation

Member 3's inspected demand-forecasting trainer is still a placeholder. This
milestone therefore establishes independently testable federation mechanics
using a synthetic two-parameter linear model. It does not replace Member 3's
model or claim healthcare prediction accuracy.

## Run from infra/

```powershell
.\.venv\Scripts\python.exe -m federated --rounds 5
```

Output contains round summaries, final global parameters, regional metadata and
initial/final local training errors. Logs go to stderr. No server is started or
artifact written by default, and no dependency is installed. Optional
[checkpoint saving/recovery](federated-checkpoints.md) is now supported.
Python's standard library is
sufficient. `--rounds` supports 1..100 rounds.

## Round process

1. The coordinator exposes a global model, version and next-round number.
2. Each local client trains its copy on its own synthetic samples.
3. Each returns an update containing node ID, input model version, model schema,
   round, sample count, training duration, parameters and local training error.
4. The coordinator validates packets and accepts only registered node IDs.
5. If at least the configured minimum participates, sample-weighted averaging
   produces the next model; otherwise the model/version remain unchanged.

For parameter theta, FedAvg uses `sum(n_i * theta_i) / sum(n_i)` across accepted
participants. The demo has three regions with different feature distributions
and sample counts, and a two-client minimum. Configuration is packaged in
`federated/configs/demo.json`.

The update contract is deliberately strict: unknown fields (including raw sample
payloads), wrong versions/schemas, non-finite parameters, invalid sample counts
and incompatible rounds are rejected. Duplicate participant identities abort the
round before any state change. Invalid packets are individually rejected;
enough remaining valid participants can still complete the round.

Every processed attempt increments the round number, even if the minimum is not
met. Model versions advance only after aggregation. This prevents an old round's
packet from being reused in the next attempt. Malformed batch envelopes and
duplicate participants abort without advancing state.

## Client/coordinator boundary

`SyntheticClient` owns its local sample array. Its packet contains no raw records.
The coordinator receives model updates and aggregate metrics only; after a round
it retains the global model and node metadata, not individual parameter updates.
Metadata includes region, latest participation status, last valid observation,
round, sample count, input model version, duration and metric summary. Missing
nodes keep their previous observation metadata with current status `missing`.

All objects run in one process, and the demo harness creates the synthetic data.
This is a logical interface boundary, not operating-system isolation. Allowlisted
IDs are not authenticated identities. The coordinator sees clear individual
updates during aggregation; model updates can leak information. There is no
secure aggregation, differential privacy, poisoning defense or verifiable sample
count. Finite-value bounds are input validation, not a security guarantee.

`weighted_local_training_mse` averages errors of each client's different locally
trained model. It is not the global model's evaluation score. Final demo errors
evaluate the global model on each client's training samples, not held-out data.
Improvement on synthetic training samples does not establish generalization.

## Next integration steps

- Implemented: versioned checkpoint saving and restore verification; see the
  checkpoint guide for atomic-write and integrity limitations.
- Agree with Member 3 on model tensors/schema, feature ordering, preprocessing,
  training objective, permitted metrics and held-out regional evaluation.
- Adapt client/coordinator execution to Flower/PyTorch and isolated regional
  processes with authenticated, encrypted communication.
- Add real deadlines/availability monitoring. The current synchronous API only
  handles absent packets at the time `aggregate_round` is called; it does not
  enforce network timeouts, coordinate concurrent rounds or detect live liveness.
- Add privacy mechanisms and accounting only after the basic model flow works.

Six focused tests verify exact sample weighting, state/copy isolation, minimum
participation and recovery, duplicate rejection, malformed/stale packets, client
payload boundaries and a complete five-round synthetic run. No broader suite or
network service was run for this milestone.
