# Sequential safe-surplus simulation

Unlike independent what-if scenarios, timeline mode carries remaining source stock
forward after each simulated arrival, delivery, explicit loss and expiry event. It changes
only an in-memory copy of the supplied snapshot. It does not approve or dispatch
real transfers.

From `infra/`:

```powershell
.\.venv\Scripts\python.exe -m optimization.simulation --timeline --demo
.\.venv\Scripts\python.exe -m optimization.simulation --timeline --input optimization/simulation/timeline-example.json
.\.venv\Scripts\python.exe -m optimization.simulation --timeline --input optimization/simulation/replenishment-example.json
```

Provide `baseline` in the existing redistribution-v1 format, optional `policy`,
and 1–365 `periods`. Each period contains:

- `day`: a strictly increasing integer offset from the baseline, within 0–3650.
- `demand`: that period's required quantity, supplied by the caller.
- Optional `blocked_sources`: distinct known facility IDs unavailable that period.
- Optional `losses`: objects with `facility_id` and nonnegative `quantity`, bounded
  by that source's remaining unexpired safe surplus. Each facility appears once.
- Optional `arrivals`: objects with `facility_id`, `batch_id`, positive
  `safe_surplus` and positive `expiry_days` measured at arrival. Each facility
  appears at most once per period and must already exist in the baseline.

Processing order is expiry, arrivals, explicit losses, then allocation and hypothetical
immediate delivery. Remaining expiry of zero or less removes stock from the ledger.
Stock below the policy's minimum shelf life stays in the ledger until actual expiry,
but the optimizer cannot allocate it. Blocking a source preserves its stock for
later periods; blocking must be repeated if an outage continues.
Blocking represents outbound access only: an arrival still enters stock on a
blocked day. To simulate an inbound supplier delay, move the arrival to a later
period explicitly. Losses can remove stock received earlier in that same period.

One active batch per source is supported. A new batch may replace the old batch
only when its remaining stock is zero after expiry processing. A top-up of the
current batch must preserve its absolute expiry day. Previously replaced batch
IDs cannot be reused. This prevents silently extending expiry or merging batches
with different shelf lives. Arrival quantities must already exclude reservations
and protected safety stock; they are newly available surplus, not total deliveries.

Each period reports opening/closing safe surplus by source, expiry, losses,
simulated deliveries and the recommendation. An invariant verifies for every source:

`opening + arrived = closing + delivered + lost + expired`

The result uses version `safe-surplus-timeline-v2`, adds `totals.arrived`, and records
arrival amounts and closing batch identity/absolute expiry day per source. Existing
inputs without arrivals remain supported and retain their previous stock outcomes.

Results also contain aggregate delivered quantity, unmet demand, cost, an input
digest and explicit model assumptions. Identical inputs replay deterministically.
No UUID/time-based live recommendation identity is generated in the final output.

The example starts with 1500 units, delivers 1300 across three periods, loses 100,
expires 100 and ends with zero surplus. Total unmet demand is 300 units.

This tracks **transferable surplus**, not the entire hospital inventory. Protected
safety stock, source consumption, destination storage, road travel
delays and forecasts are not modeled. Deliveries are assumed consumed in the same
period. Unmet demand is not carried forward, and unlisted days have no demand events.
It is a limited dynamic simulation component, not the full digital twin.

Five focused checks passed for conservation, temporary blocking, arrival expiry,
supplier delay, batch/expiry validation, replay, input isolation and invalid
days/losses. No full suite or training ran.

```powershell
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_timeline -v
```
