# Member 4 implementation roadmap

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

Next: connect emergency priority with constrained resource recommendations.
Confirm the provisional normalization contract with Member 3. Live model
integration remains pending. Add constrained workforce and procurement support.
Agree on resilience score semantics before implementing its orchestration.

## Milestone 5 — federated learning

Integrate a Member 3 model using Flower/PyTorch, three simulated clients, FedAvg,
per-region evaluation, checkpoints, node status, and dropout tests. Then add
privacy accounting, secure aggregation, and optional local personalization.

## Milestone 6 — simulation

Use isolated facility/stock snapshots. Compare baseline and disruptions, record
scenario configuration and seeds, and rerun forecasting and optimization.

## Infrastructure throughout

Start Compose once service contracts exist. Add linting, image builds and scans,
staging deployment, protected monitoring, secrets management, service identity,
and tested backup/restore. Keep production deployment a separate approved action.

## Before each pull request

Sync with the team's integration branch; inspect changes; run relevant tests;
check for secrets; document input/output changes; coordinate shared-file edits.
Do not assume a local CI pass means a hosted workflow or deployment has run.
