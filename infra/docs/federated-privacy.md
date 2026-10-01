# Privacy and masked aggregation reference

A separate synthetic prototype now implements clipped/noisy client updates,
privacy-budget accounting and fixed-roster masked aggregation. Run from `infra/`:

```powershell
.\.venv-federated\Scripts\python.exe -m federated.privacy --rounds 3
# After building the federation image on a Docker-capable host:
docker compose -f compose.yaml run --rm --no-deps federation-privacy-demo
```

The Docker demo has no network and mounts no credentials. The original FedAvg,
regional subprocess and HTTPS runners are unchanged: they still transmit clear
individual model parameters inside their transport. This prototype is not silently
enabled for those paths and is not approved for real health data.

## Clipping, noise and budget

`federated/configs/learning.json` now configures enablement and clipping norm C, noise multiplier sigma, delta
and maximum epsilon (`privacy_budget`). `privacy/policy.json` remains a legacy policy fixture. Each client computes a two-coordinate model delta, clips
its L2 norm to C, and adds independent Gaussian noise with standard deviation
`2 * C * sigma` per coordinate. The privacy unit is replacing one client's entire
local dataset with the same public participant roster. Two clipped vectors differ
by at most 2C. Sample counts and local loss values are not sent to aggregation.
Weights are equal per client, not proportional to private sample counts.

For the ideal Gaussian mechanism, each release costs `rho = 1/(2*sigma^2)` zCDP.
The accountant adds rho across releases for the same client and converts with
`epsilon = rho + 2*sqrt(rho*log(1/delta))`. It refuses a release exceeding the configured
cap. Aborted aggregation does not refund a locally released update. Composition
is per client across rounds, not a sum over different disjoint clients. These
calculations follow [Bun and Steinke's zCDP analysis](https://arxiv.org/abs/1605.02065).

The implementation uses OS-backed random sampling through `SystemRandom` with
floating-point Gaussian arithmetic. The bound describes the ideal mechanism; a
finite-precision privacy/security audit has not been performed. Default session mode resets counters. Optional SQLite mode charges durably before
sampling, serializes concurrent reservations and refuses changed policy/roster or
missing/corrupt ledgers. Audited sampling, agreed adjacency and rollback-resistant
storage remain production requirements. Coordinate bounding and quantization
after noise are fixed post-processing operations.

## Masked aggregation

Every round generates new X25519 key pairs at each client. Pairwise DH secrets pass
through HKDF with a session/roster transcript. Opposite-sign pairwise masks are
added to two fixed-point coordinates modulo 2^128, then cancel when every member's
packet is summed. The aggregation API receives public keys and masked vectors;
it returns the equally weighted average with at most 0.5e-6 quantization error
per coordinate relative to the average of supplied bounded vectors.

At least three participants are required. Duplicate identities, stale transcripts,
key reuse, malformed vectors and incomplete rosters fail. Any dropout aborts;
there is no reconstruction or partial aggregation. Follow the
[X25519 key-derivation guidance](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x25519/).

This is an architectural demonstration of pairwise masking, **not** the full
[dropout-tolerant secure aggregation protocol](https://research.google/pubs/practical-secure-aggregation-for-privacy-preserving-machine-learning/)
or Flower SecAgg+. The trusted harness supplies one common public-key roster.
The current harness adds pinned Ed25519 identities, signed ephemeral-key exchange
and signed updates bound to nonce/round/model version; altered signatures and
replay are rejected. Independent identity enrollment, coordinator/client collusion
defense, Sybil defense and poisoned-update detection are not implemented.
All clients share one Python process, so the harness can inspect their memory.
Aggregate-only API access must not be confused with OS isolation or formal guarantees.

## Utility and checks

The demo compares noisy aggregate training with an equal-weight nonprivate control,
evaluated only on a public synthetic grid. No private training loss is released.
Noise can worsen utility substantially with three clients; this is reported rather
than hidden. The control path is permissible only because every input is synthetic.

Three focused checks passed: clipping/noise calibration and budget refusal,
mask cancellation and fail-closed dropout/replay/key reuse, and combined synthetic
execution. No external model or long training run was used. A production privacy
claim remains explicitly false in demo output until the listed gaps are resolved.

## Explicit durable synthetic workflow

Initialize a NEW ledger once, then run without initialization:

```powershell
docker compose -f compose.yaml -f compose.privacy.yaml run --rm --no-deps federation-privacy-demo privacy --ledger federated/checkpoints/privacy.sqlite --initialize-ledger --rounds 1
docker compose -f compose.yaml -f compose.privacy.yaml run --rm --no-deps federation-privacy-demo
```

The `privacy-budget` volume survives container replacement. On this host it is
already initialized: use only the second command. Initialization refuses existing
files. Never delete/roll back a ledger to bypass exhaustion. Two fresh containers
advanced all counts from 1 to 2 (`outputs/privacy-persistence.json`). Model weights
restart for each synthetic invocation; lifetime release counts continue. Failed
rounds may leave different counts, independently charged and reported. Commits
precede sampling; privileged editing/deletion and rollback are not prevented.
The direct CLI supports these flags under `infra/federated/checkpoints/`.

## October 1 configuration additions

Optional node-local personalization and public region/country metadata are documented
in [the completion guide](completion-and-deployment.md). Personalization never
modifies the global model or sends personalized weights to the coordinator.
