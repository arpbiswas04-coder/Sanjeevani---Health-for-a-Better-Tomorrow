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

`privacy/policy.json` configures clipping norm C, noise multiplier sigma, delta
and maximum epsilon. Each client computes a two-coordinate model delta, clips
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
finite-precision privacy/security audit has not been performed. Budgets are
in-memory for one demo session; repeated runs must not be treated as fresh budgets
on real data. A durable per-client ledger, agreed adjacency and audited sampling
are prerequisites for production integration. Coordinate bounding and quantization
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
There is no authenticated peer-key exchange, protection against malicious roster
substitution, coordinator/client collusion, Sybil identities or poisoned updates.
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
