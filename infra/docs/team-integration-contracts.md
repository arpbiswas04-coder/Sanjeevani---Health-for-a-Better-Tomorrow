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
