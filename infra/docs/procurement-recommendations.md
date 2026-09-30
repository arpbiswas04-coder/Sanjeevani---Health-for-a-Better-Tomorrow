# Procurement support for unresolved shortages

Implemented in `optimization/procurement/` using the existing OR-Tools install.
It recommends purchases; it never submits a purchase order, contacts a supplier,
reserves budget or changes inventory. The inspected backend has no procurement
models yet; live integration remains Member 2 work.

## Run from infra/

```powershell
.\.venv\Scripts\python.exe -m optimization.procurement --demo
```

The synthetic example needs 25 tablets. It recommends three 10-unit packs from
supplier A for 350 paise including one delivery fee, covering the shortage with
five permitted surplus units. With surplus disallowed it can instead purchase
exactly 25 for 390 paise. These are demonstration prices, not real quotations.

```python
from optimization.procurement import recommend_procurement

result = recommend_procurement(request, max_age_seconds=3600, time_limit_seconds=5)
```

## Contract

See `optimization/procurement/example.json`. The request identifies a shortage
snapshot, capture time, destination, medicine and quantity unit. It supplies
remaining required quantity, explicit maximum overstock, budget in INR paise,
maximum delivery lead time and minimum shelf life on arrival.

Each supplier quote states approval status, medicine/unit, units per pack,
available packs, positive minimum order in packs, price per pack, fixed delivery
fee, lead time, shelf life on arrival, observation time and quote expiry.
One quote per supplier is supported. Medicine IDs must already distinguish
strength/formulation and quotes must apply to the named destination. All prices
must include taxes/other charges except the separately declared delivery fee;
discounts and tiered pricing are not modeled.

The backend must compute shortage after approved/reserved redistribution and
account for confirmed incoming stock and existing orders. Deducting merely
proposed transfers can understate the real shortage; ignoring existing orders
can cause duplicate purchases. Snapshot references are trusted inputs, not a
database lookup by this module.

## Constraints and objective

Only approved, matching, fresh, unexpired quotes arriving within the deadline
and with enough shelf life are eligible. Quotes observed after the snapshot are
excluded. Per-supplier packs are integer, bounded by availability, and either
zero or at least the minimum order. Fixed delivery fees apply once per used
supplier. Total spend cannot exceed the budget; total units cannot exceed the
shortage plus explicit overstock allowance. Zero shortage never creates orders.

Objective order: maximize covered shortage, then minimize purchase cost, then
minimize purchased units to avoid gratuitous overstock among equal-cost plans.
Each later phase runs only after proving the previous optimum. A timeout retains
the latest feasible recommendation without falsely claiming minimum cost.

One medicine/destination per call. There are no shared multi-item shipping costs,
multi-destination orders, joint supplier capacity across concurrent requests,
currency conversion or supplier reliability predictions. Quantity/cost and array
limits bound the integer model. Lead-time promises are supplied, not forecast.

## Response and approval

Output contains pack/quantity recommendations, itemized supplier cost, shortage,
overstock, remaining budget, exclusions, solver phases and proven objectives.
`recommended` means an incumbent exists; it can contain zero orders and unresolved
shortage. `no_solution` has unknown totals. `expired_during_computation` retains
output for review only. The validity deadline is the earliest shortage/selected
quote freshness or expiry bound. Reconfirm delivery timing at approval.

Member 2 must authenticate, audit, obtain approval and atomically reserve budget
and reconfirm stock/quotes before submitting orders. `now=` is for tests; real
requests use the server clock. No external effects occur here.

CLI `--input request.json` preserves supplied timestamps; `--demo` refreshes only
built-in synthetic data. Exit codes: 0 feasible recommendation, 2 invalid input,
3 solver error, 4 no incumbent/expired. JSON uses stdout and logs use stderr.

Verification is limited to focused procurement tests: budget/pack/minimum-order
constraints, supplier filtering, invalid/stale inputs, timeout handling, zero
shortage/cost, and 20 cases checked by exhaustive order enumeration.
