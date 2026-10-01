# Redistribution contract v1

Paths below are relative to `infra/`. Run Python from that directory or install
the package from `infra/` into the backend environment before importing it.

This is a proposed Python/JSON contract for Member 2 integration, not an existing
HTTP endpoint. No database, authentication, approval, or dispatch is implemented.

For Member 2's existing inventory record format, use the read-only adapter
described in [backend-handoff.md](backend-handoff.md). It computes safe surplus
from explicit stock, reservation and policy inputs before invoking this engine.

## Call

```python
from optimization.redistribution import recommend, ValidationError

try:
    result = recommend(request_json, {"min_expiry_days": 7})
except ValidationError as exc:
    # Map this to the backend's standard invalid-request response.
    error_message = str(exc)
```

## Request

All fields are required. Unknown fields are rejected to catch contract mistakes.

| Field | Meaning |
| --- | --- |
| `request_id` | Caller correlation ID, not an idempotency guarantee |
| `inventory_snapshot_id` | Backend reference to the inventory snapshot |
| `shortage_facility` | Receiving facility ID |
| `medicine_id` | Medicine being requested |
| `quantity_unit` | One common indivisible unit, e.g. `tablet` or `vial` |
| `required_quantity` | Nonnegative integer deficit for the agreed time horizon |
| `candidate_sources` | Array of candidate source objects; may be empty |

Each candidate requires `facility_id`, `batch_id`, `safe_surplus`, `distance_km`,
`expiry_days`, and `transport_cost_per_unit_paise`.

- `safe_surplus`: nonnegative integer for this batch, already bounded by both
  usable unreserved batch quantity and facility-level transferable surplus.
  Member 2 must compute this using the agreed safety stock policy. The optimizer
  cannot verify safety stock from this field alone.
- Each facility can occur only once in v1, preventing repeated use of the same
  facility surplus across several batches. Multi-batch handling is deferred.
- The backend must ensure batch medicine, strength, formulation, quantity unit,
  storage/cold-chain requirements, and transfer eligibility match the request.
- `expiry_days`: integer remaining shelf life as of the snapshot. Values below
  the policy threshold are excluded. Default threshold: 1 day; example policy:
  7 days. Actual transit/use requirements must determine the real policy.
- `distance_km`: finite nonnegative number, used only to break equal-cost ties.
- `transport_cost_per_unit_paise`: nonnegative integer marginal cost per unit,
  in INR paise. Total cost is quantity multiplied by this value. Do not put a
  fixed dispatch/trip quote here. The blueprint's ambiguous `transport_cost`
  field is deliberately replaced by this explicit field.
- IDs must be nonempty strings up to 128 characters, without outer whitespace
  or control characters. Booleans and fractional quantities are rejected.

Use synthetic examples under `optimization/redistribution/examples/`.

## Optimization semantics

First maximize the fulfilled quantity, then minimize total linear transport
cost. Sort eligible sources by unit cost, distance, and facility ID; allocate up
to each source's safe surplus until the deficit is filled. An exchange argument
proves optimality for this restricted model: substituting an available cheaper
unit never worsens fulfillment or cost. Tests also compare with exhaustive search.

There are no fixed transport costs, budgets, minimum shipment quantities,
multi-stop routing, vehicle capacities, lead times, or cross-district legal or
operational permissions in this model. `optimal_for_supported_model` must never
be presented as global real-world optimality. No confidence score is invented.

## Result

- `status`: `fulfilled`, `partial`, or `unavailable`. Zero requested quantity is
  fulfilled with no transfers.
- `required_quantity = fulfilled_quantity + unresolved_shortage`.
- `recommended_transfers`: source, destination, batch, medicine, quantity, unit,
  distance, cost, and explanation for every proposed transfer.
- `excluded_sources`: candidates excluded by surplus, shelf life, or destination.
- `recommendation_id`, UTC `generated_at`, input references, schema and algorithm
  versions, applied policy, objective order, cost total, and limitations.
- `recommendation_only` and `approval_required` are always true. These flags are
  descriptive; authorization must be enforced by the backend.

Repeated calls have deterministic allocation but new recommendation IDs and
timestamps. The caller must implement retry/idempotency behavior. No input is
mutated and nothing is persisted or dispatched.

## Approval integration

Member 2 should authenticate the caller; load trusted data; invoke this module;
persist the result; expose it for authorized review; then atomically recheck and
reserve stock. Reject or recompute stale recommendations. Record approval and
transfer events in the audit trail. Snapshot IDs are references, not freshness
validation: v1 does not fetch snapshots or compare timestamps.

## CLI behavior

Results are JSON on stdout, diagnostic logs on stderr. Exit 0 means computation
succeeded (including partial/unavailable results); exit 2 means invalid input or
unreadable files. Duplicate JSON keys and non-finite constants are rejected.

`--healthcheck` checks module execution only. It is not an HTTP liveness endpoint,
dependency check, model-quality check, or authorization check.
