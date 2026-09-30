# Member 2 / Member 3 handoff contracts

Status: proposed and implemented on the Member 4 side; teammates have not yet
confirmed their service/model contracts. Their files are unchanged.

## Member 2: authenticated recommendation boundary

Call `optimization.redistribution.backend.recommend_from_inventory` (selected
batch) or its documented multi-batch counterpart with a trusted, consistent
inventory snapshot. See [backend handoff](backend-handoff.md) and
[multi-batch contract](multi-batch-redistribution.md). Responses are recommendations.
Never expose a browser's inventory or safety-stock values as authoritative inputs.

The backend must serialize IDs/dates, supply freshness and all reservation values,
authorize facility access, persist recommendation IDs, and implement approved
transfers with idempotency and an atomic availability recheck/reservation. Failed
validation maps to the backend's 4xx format; unavailable solver/dependencies are
server errors. A new route is not installed by importing this library.

## Member 3: proposed demand forecast envelope

The callable adapter is `optimization.simulation.forecast.simulate_forecast`:

```python
result = simulate_forecast(inventory_baseline, forecast_envelope)
```

Required forecast fields:

```json
{
  "forecast_id": "forecast-001",
  "model_version": "demand-model-v1",
  "generated_at": "2026-09-30T00:00:00Z",
  "inventory_snapshot_id": "synthetic-snapshot-001",
  "destination_id": "fac-10",
  "medicine_id": "med-22",
  "quantity_unit": "tablet",
  "periods": [{"day": 0, "demand": 100}, {"day": 1, "demand": 200}]
}
```

The timestamp is illustrative; real calls need fresh values. The default maximum
forecast age is one day (configurable up to seven). Future/stale forecasts fail.
Inventory snapshot ID, destination, medicine and unit must match exactly. Day zero
means the initial inventory snapshot day; entries have strictly increasing offsets,
at most 365 periods within 3650 days. Demand must be an explicit nonnegative integer
in the same unit; conversion/rounding of model means is Member 3's agreed policy,
not silently guessed here. Each value is that period's residual transfer demand,
not cumulative demand or total patients. Destination-held inventory must already
be accounted for upstream. Missing days have no modeled demand.

The result is a synthetic timeline recommendation with forecast provenance. It
does not execute stock transfers or verify model accuracy. The adapter rejects
unknown fields, mixed contexts and fractional quantities. One focused check covers
valid mapping and stale/unit/medicine mismatches.

## Federation model integration contract to agree

Member 3 must supply model architecture and versioned tensor shapes/dtypes, a safe
artifact format/checksum, feature/target schema, preprocessing version, local
train/evaluation split, permitted metrics and model acceptance criteria. Do not
load an arbitrary pickle or infer compatibility from a filename. Current code's
`synthetic-linear-v1` two-coordinate schema is not a real healthcare model.

Agree on privacy unit, public cohort/weights, permitted releases, lifetime privacy
budget, local ledger persistence and secure peer-key exchange before connecting a
real model to the [privacy reference](federated-privacy.md). Existing clear-update
HTTPS paths do not gain privacy guarantees automatically.

## Complete boundary index

| Input/output | Member 4 callable / guide | Upstream owner |
| --- | --- | --- |
| Inventory | `optimization.redistribution.backend.recommend_from_inventory`; backend-handoff.md | Member 2 stock, reservations, safety floors and approval |
| Forecast | `optimization.simulation.forecast.simulate_forecast` | Member 3 provenance/horizon/units; Member 2 matching snapshot |
| Risk/EPI | `optimization.emergency.score_emergency_priorities`; emergency-priority.md | Member 3 versioned normalized signals and observation times |
| Emergency allocations | `optimization.emergency.resources.recommend_emergency_resources` | Fresh compatible scores and stock |
| Staff | `optimization.workforce.engine.recommend_staff`; workforce-redistribution.md | Member 2 verified skills/roles/rest, minima and shift/travel coverage |
| Ambulances | `optimization.ambulance.recommend_ambulance`; ambulance-allocation.md | Member 2 fleet readiness/reservations/ETA/equipment and authorized dispatch |
| Routes | `optimization.routing.engine.recommend_routes`; vehicle-routing.md | Trusted directed matrices, capacities and time windows |
| Procurement | `optimization.procurement.engine.recommend_procurement`; procurement-recommendations.md | Trusted offers, budget/deadlines; approval external |
| Resilience | `optimization.simulation.resilience.assess_resilience`; resilience-orchestration.md | Versioned scenario weights; team validation |
| Models | Safe artifact contract above | Member 3 preprocessing, eligibility and acceptance criteria |

All examples are synthetic. Member 2 owns authorization, idempotency, expiry,
record persistence, human approval and transactional rechecks. Never silently
refresh real timestamps, infer clinical policy or replace missing signals with zero.
