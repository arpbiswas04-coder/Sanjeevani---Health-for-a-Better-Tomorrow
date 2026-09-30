# Member 4 implementation roadmap

Current acceptance status: see `docs/member4-handoff.md`. Ten small synthetic CLI
demos passed through `delivery.py --demo`; this is not a claim that privacy,
full-stack integration or production deployment is complete.

All paths in this roadmap are relative to the root `infra/` directory. Keep
Member 4 source code, configuration, tests, and documentation in that directory.

## Milestone 1 — standalone redistribution (implemented)

- Strict request and policy validation.
- Single destination and medicine, one batch per distinct source facility.
- Maximize fulfillment, then minimize linear per-unit transport cost.
- Expiry filtering, safe-surplus bounds, partial results, and explanations.
- Recommendation-only output, snapshot references, tests, and a CI template.
- The CI template at `ci-cd/member4-ci.yml` is inactive: activation requires the
  team to place it under the repository root `.github/workflows/` directory.

## Milestone 2 — backend integration

Implemented: read-only inventory adapter, snapshot-age validation, explicit
reservation/safety-stock handling, backend response envelope, focused tests, and
`docs/backend-handoff.md`. Remaining: live route, persistence, authorization,
approval, and atomic reservation integration in Member 2's backend.

Agree on actual routes and schemas with Member 2. Persist recommendations in the
backend; enforce authorization, approval, idempotency, expiration, atomic stock
rechecks and reservations there. Replace synthetic data with eligible inventory
snapshots and add integration tests. Expose backend readiness/health endpoints.

## Milestone 3 — richer optimization

Implemented: `recommend_all_batches` with shared facility safety-stock caps,
reservation-aware batch quantities, and earliest-expiry allocation within each
facility. V1 callers retain their selected-batch behavior. See
`docs/multi-batch-redistribution.md` for the v2 contract and focused tests.

Implemented next: `optimization/transport/` adds multi-destination constraints,
shared stock limits and fixed per-lane dispatch charges with two-stage OR-Tools
CP-SAT and explicit incumbent/optimality reporting. See `docs/transport-optimization.md`.

Implemented next: `optimization/routing/` adds single-depot routes with directed
travel/distance matrices, capacities, service windows, shifts, waiting and
unserved stops. See `docs/vehicle-routing.md`. Multi-depot and joint
allocation/routing integration remain pending.

Implemented next: `optimization/ambulance/` adds eligibility filtering, ETA-based
ranking, alternatives, freshness checks and a backend handoff contract. Live
fleet integration and atomic reservation/dispatch remain Member 2 work.

Emergency priority scoring is now implemented in Milestone 4. Keep the current restricted optimizer as an independently testable
baseline; do not apply its greedy rule to richer constraints.

## Milestone 4 — emergency and operational support

Implemented: `optimization/emergency/` provides versioned configurable EPI
weights, normalized input validation, contribution breakdown, ranking, freshness,
and explicit unscored missing-data outcomes. See `docs/emergency-priority.md`.

Implemented: emergency resource orchestration connects fresh scores to transport
through maximum fulfillment, priority-weighted fulfillment and minimum cost.
Missing/stale scores block the plan. See `docs/emergency-resource-recommendations.md`.

Implemented: `optimization/workforce/` recommends single-shift staff assignments,
protecting source staffing by role and enforcing skills, eligibility and
round-trip availability. See `docs/workforce-redistribution.md`.

Implemented: `optimization/procurement/` recommends integer-pack purchases for
remaining shortages under budget, supplier eligibility, minimum orders,
delivery deadlines and shelf-life limits. See `docs/procurement-recommendations.md`.

Confirm the provisional normalization contract with Member 3. Live model
integration remains pending. Workforce and procurement modules are implemented.
Agree on resilience score semantics before implementing its orchestration.

## Milestone 5 — federated learning

Added: bounded multi-round client polling, stale-training discard, explicit timeout
and no automatic retry of ambiguous submissions. Available through direct/local
CLI and Docker client settings. Three scheduling checks passed without training;
see `docs/federated-round-runner.md`.

Implemented: standard-library synthetic local clients, coordinator, sample-weighted
FedAvg, round/model validation, minimum-participant handling, node metadata and
six focused tests. See `docs/federated-foundation.md`. This is an in-process
reference model, not Flower/PyTorch or a healthcare model integration.

Implemented: versioned JSON checkpoints with checksums, atomic replacement,
strict restore validation and CLI resume. Six focused recovery checks passed;
see `docs/federated-checkpoints.md` for durability/security limits.

Implemented: optional Flower NumPyClient/PyTorch adapters, three local regional
subprocesses, synthetic held-out evaluation and checkpoint reuse. See
`docs/flower-pytorch-regional.md`. This does not start Flower's network runtime.

Implemented: opt-in signed update admission with distinct node keys, round
challenges, replay/timestamp validation and serialized round closing. Three
focused security checks passed. See `docs/federated-authentication.md`.
Existing local demos do not yet use this authentication boundary.

Implemented: private-development mutual-TLS HTTPS service and regional client,
certificate-to-update identity binding, bounded update bodies, timed round closing
and checkpoint recovery. See `docs/federated-https.md`. This custom transport
reuses the Flower/PyTorch adapter; it does not run Flower's network runtime.

Implemented: local-only credential provisioning, restricted secret directory,
seven-day certificates, separate per-node HMAC keys and role-specific launch
helpers. See `docs/federated-local-setup.md`. One focused provisioning check passed;
no persistent credentials or running service were left by validation.

Next: production credential lifecycle/deployment hardening and Member 3 model integration.

Integrate a Member 3 model using Flower/PyTorch, three simulated clients, FedAvg,
per-region evaluation, checkpoints, node status, and dropout tests. Then add
privacy accounting, secure aggregation, and optional local personalization.

## Milestone 6 — simulation

Implemented: baseline-versus-alternative timeline comparison on a shared snapshot,
policy and day grid. Includes per-day shortage/delivery deltas, full traces and
summary metrics with explicit zero-demand semantics. Two focused checks passed;
see `docs/timeline-comparison.md`. No resilience score is inferred.

Implemented: sequential safe-surplus ledger with simulated deliveries, per-period
blocking, permanent losses, expiry and per-source conservation checks. Two focused
checks passed. See `docs/inventory-timeline.md`. Destination storage,
travel delays and forecast integration remain pending; this is not a complete twin.

Added: explicit replenishment arrivals and supplier-delay modeling in timeline v2,
arrival-inclusive conservation, per-source closing batch metadata and safeguards
against mixed batches or expiry resets. Five timeline checks passed. One active
batch per source remains the supported limit.

Implemented: isolated baseline-versus-scenario comparisons using redistribution v1,
with demand changes, source outages, surplus loss, cost changes and expiry aging.
Includes replay digest, transformed snapshots, shortage/cost deltas and two focused
checks. See `docs/scenario-simulation.md`. Dynamic stock evolution, forecasts,
multi-resource orchestration and resilience scoring remain pending.

Use isolated facility/stock snapshots. Compare baseline and disruptions, record
scenario configuration and seeds, and rerun forecasting and optimization.

## Infrastructure throughout

Implemented: configurable per-certificate-identity request budgets in the HTTPS
service, HTTP 429/Retry-After, bounded limiter state and throttling metrics. Four
focused checks passed. See `docs/federated-rate-limits.md`. Pre-authentication
connection controls and production HTTP runtime hardening remain pending.

Added to the inactive CI template: separate transport/federation dependency audits,
federation image build and HIGH/CRITICAL vulnerability gate, with retained reports.
Only static configuration checks performed; activation and actual scan results
remain pending. See `docs/security-scanning.md`.

Added: on-demand encrypted federation state backup, authenticated verification
and restore to a new checkpoint without overwriting existing files. One focused
round-trip/tamper/wrong-key/no-overwrite check passed. See `docs/federated-backup.md`.
Database/object-storage backups, off-host retention and operational recovery drills
remain pending.

Added: monitoring-certificate-only Prometheus metrics, operational round/update
counters, checkpoint timestamps, node-status counts, optional Compose monitoring
overlay and three alert rules. Focused authorization/metrics checks passed;
container scraping and alert evaluation remain unverified without Docker/promtool.
See `docs/federated-monitoring.md`. Alert delivery remains pending.

Added: optional Grafana Compose overlay, file-based admin password, provisioned
datasource and eight-panel federation dashboard. Static YAML/JSON checks passed;
container startup and rendering remain unverified. See `docs/federated-grafana.md`.

Added: a separate `infra/compose.yaml` with a non-root federation image,
coordinator, three on-demand clients, read-only per-role credentials, persistent
checkpoints and listener healthcheck. Static checks passed; Docker is unavailable
on the implementation host, so builds/runtime remain unverified. See
`docs/federated-docker.md`. The complete application stack remains pending integration.

Verify the supplied Member 4 Compose stack on a Docker-capable host and integrate
the team services once contracts are agreed. Add linting, execute image builds and scans,
staging deployment, protected monitoring, secrets management, service identity,
and tested backup/restore. Keep production deployment a separate approved action.

## Before each pull request

Sync with the team's integration branch; inspect changes; run relevant tests;
check for secrets; document input/output changes; coordinate shared-file edits.
Do not assume a local CI pass means a hosted workflow or deployment has run.
