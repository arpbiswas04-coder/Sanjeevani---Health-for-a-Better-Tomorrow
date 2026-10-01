# Multi-batch redistribution v2

The new `recommend_all_batches` function uses all eligible inventory batches
from each source facility. The v1 function and standalone CLI remain unchanged.

## Call

Use the snapshot format in [backend-handoff.md](backend-handoff.md), but remove
`selected_batch_id` from every source. Keeping that field is rejected to avoid
silently ignoring a caller's intended batch restriction.

```python
from optimization.redistribution.backend import recommend_all_batches

response = recommend_all_batches(snapshot, {"min_expiry_days": 7})
```

Run from `infra/` or install its Python package into the backend environment.
The response remains `{"success": true, "data": ...}`; data now has schema
version `2.0` and algorithm version `facility-linear-fefo-v2`. Each transfer has
an actual batch ID, inventory row ID, quantity, remaining shelf life and cost.
No synthetic facility-pool batch IDs are exposed.

## Allocation rules

1. Validate snapshot freshness, complete inventory, explicit reservations,
   active facilities, batch identities, medicine and shelf-life policy.
2. Subtract each eligible batch's reservations from its stock.
3. For each facility, cap total exports at
   `max(0, eligible unreserved stock - safety stock)`.
4. Maximize fulfillment, then minimize linear per-unit facility transport costs.
5. Split each facility allocation across its eligible batches in earliest-expiry
   order, breaking ties by batch ID. This is FEFO within a facility, not global
   FEFO across differently priced facilities.

Example: batch A has 800 units with 100 reserved; batch B has 200 units; safety
stock is 300. Together they can export at most **600**, not 600 from each batch.
If B expires first, allocate its 200 units then 400 from A. If safety stock is
zero and demand is 850, allocate 700 from A and 150 from B when A expires first.

Safety stock is conservatively retained entirely from eligible, unreserved
stock. Already insufficient facilities export nothing; existing deficiencies
are not repaired by this rule. Eligibility exclusions and calculation details
are included in the output. Source and destination may not transfer to themselves.

## Scope and correctness

Facility-level unit costs are identical for every batch at that facility. This
allows exact selection by facility capacity and cost, followed by lossless batch
expansion. No third-party solver is necessary for this restricted model.

Fixed dispatch costs, multiple destinations, batch-specific costs, pack-size
constraints, vehicle capacity and travel windows still require a richer model.
The next step is an OR-Tools-backed transport/routing model. Do not reinterpret
the per-unit input as a trip quote or use this greedy rule for fixed costs.

Approval, atomic stock rechecks, persistence, idempotency, and inventory writes
remain Member 2 responsibilities. This function only returns recommendations.

## Verification

From `infra/`, run the adapter and multi-batch tests because they share validation:

```powershell
python -m unittest optimization.tests.test_backend_adapter optimization.tests.test_multi_batch -v
```

The new tests include 60 small cases checked against exhaustive allocation under
per-batch and shared facility capacities, plus expiry, reservation, recall,
determinism and backwards-compatibility checks.
