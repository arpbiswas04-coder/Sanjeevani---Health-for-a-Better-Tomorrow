# Multi-destination transport allocation

Implemented under `optimization/transport/`, using OR-Tools CP-SAT. This is a
recommendation engine for one medicine and common indivisible quantity unit.
It selects quantities and source-destination connections, not road routes.

## Run from infra/

The isolated `.venv` on this machine now contains OR-Tools. In PowerShell:

```powershell
.\.venv\Scripts\python.exe -m optimization.transport --input optimization/transport/example.json
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_transport -v
```

For another machine, create a Python 3.11+ environment and install the optional
package extra from `infra/`: `python -m pip install ".[transport]"`.
Redistribution v1/v2 still require no external dependencies.

The sample fulfills 70 units for PHC A and 30 for PHC B from warehouse B, costing
420 paise total. Warehouse A has a cheaper per-unit price, but its fixed charges
make it more expensive. These are synthetic demonstration prices.

## Python and JSON contract

```python
from optimization.transport import recommend_transport

result = recommend_transport(request, time_limit_seconds=5, min_expiry_days=7)
```

See `optimization/transport/example.json` for the complete request. Required:

- `request_id`, `inventory_snapshot_id`, `medicine_id`, `quantity_unit`.
- `sources`: unique facility IDs, shared `safe_surplus`, and batches containing
  `batch_id`, `available_quantity`, and `expiry_days`.
- `destinations`: unique facility IDs and nonnegative `required_quantity`.
- `lanes`: allowed source/destination pairs, `capacity`, `unit_cost_paise`, and
  `fixed_dispatch_cost_paise`. Omitted pairs cannot transfer stock.

All quantities/costs are nonnegative integers up to one billion. Sources and
destinations must be disjoint; this version does not support transshipment.
Array and aggregate-cost limits prevent unsupported model sizes/integer ranges.

The trusted backend must provide fresh stock, deduct reservations, exclude
recalls/inactive facilities and incompatible medicine/storage combinations,
and calculate safety-stock-protecting surplus. This normalized API does not
load database records or validate snapshot age. The previous backend adapter
is still a single-destination adapter; multi-destination database integration
remains pending. Do not submit separate independent plans for the same snapshot
and assume they reserve stock across calls.

## Model

For every allowed connection, an integer quantity is linked to a binary
dispatch indicator. The indicator is one exactly when quantity is positive.

1. Maximize total fulfilled quantity under source, destination and lane caps.
2. Once maximum fulfillment is proven, fix that quantity and minimize total
   variable cost plus fixed charges.

One fixed charge is paid per **used source-destination pair**, irrespective of
the number of batches. It is not charged for unused connections, and does not
represent several trips or a shared multi-stop vehicle. Each source's quantities
are expanded into actual batch transfers in earliest-expiry order; destinations
are expanded in ID order. Batch eligibility/cost must be the same for every
destination using the lane model. Destination-specific shelf life is not modeled.

With insufficient supply, all requested units have equal priority. There is no
fairness or emergency priority guarantee. A time-window/vehicle-routing engine
and operational emergency policy are later milestones.

## Solver and timeout semantics

`time_limit_seconds` is a combined solver-time budget (0 < limit <= 60), default
5 seconds. Validation, model construction, and serialization add overhead;
this is not a hard request deadline.

- `solver_status: optimal`: both fulfillment and cost are proven optimal.
- `solver_status: feasible`: a valid incumbent exists, but the full objective
  is not proven. Inspect `fulfillment_optimal`, `cost_optimal`, and `phases`.
- `solver_status: no_solution`: no incumbent returned; totals and shortages
  are null, status is `not_computed`, and no recommendation may be executed.
- If phase one finds only a feasible result, phase two is skipped.
- If phase two cannot return an incumbent, retain the proven-fulfillment phase
  one solution and do not claim minimum cost.

An optimal all-zero allocation for disconnected destinations means genuinely
unavailable supply in this model; it differs from no solution found in time.
Equal-quality solutions can differ across OR-Tools versions.

Costs are itemized on `dispatches`; `recommended_transfers` contains actual
batch quantities without duplicating fixed charges. Per-destination shortages,
excluded batches, policy, input references, and approval flags are returned.
Backend approval, atomic inventory rechecks/reservations, idempotency and audit
logging are still required. This engine never changes stock.

CLI exit codes: 0 for a solution (including partial/unavailable), 2 for invalid
input, 3 for missing solver/model failure, 4 for no incumbent. Logs use stderr,
result JSON uses stdout. There is no long-running service.

## Verification and reference

Tests compare 40 small instances against exhaustive enumeration, exercise shared
stock and batch caps, fixed-charge selection, expiry, disconnected destinations,
input validation, and controlled solver-limit outcomes. The CLI is smoke-tested.

Implementation follows the official [OR-Tools CP-SAT status and integer-model
documentation](https://developers.google.com/optimization/cp/cp_solver).
