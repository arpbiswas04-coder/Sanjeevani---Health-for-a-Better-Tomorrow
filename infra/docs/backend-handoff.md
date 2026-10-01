# Backend adapter handoff

Implemented in `optimization/redistribution/backend.py`, entirely under `infra/`.
Inspected backend reference: local `backend/member-2` clone at commit `6677eaa`.
This adapter is callable Python code, not an installed HTTP route or database
integration. It does not grant approval, reserve stock, or create transfers.

This page documents the v1 selected-batch API. The new
[multi-batch v2 API](multi-batch-redistribution.md) uses the same snapshot format
without `selected_batch_id`, and allocates across all eligible batches.

## Existing backend mapping

| Backend record | Adapter use |
| --- | --- |
| Facility `id`, `active` | Source/destination identity and eligibility |
| Medicine `id`, `unit` | Requested medicine and common quantity unit |
| Inventory `id`, `facility_id`, `batch_id`, `quantity` | Stock and reservation reference |
| Nested batch `id`, `medicine_id`, `expires_on`, `recalled` | Batch consistency and eligibility |

Pass serialized JSON records, as returned by the backend API. IDs and expiry
dates must be strings; raw SQLAlchemy UUID/date objects require serialization.
Additional record metadata is accepted. Wrapper fields are strictly validated.

## Call from an authenticated backend service

```python
from optimization.redistribution.backend import recommend_from_inventory

response = recommend_from_inventory(snapshot, {"min_expiry_days": 7})
# response == {"success": True, "data": recommendation}
```

Install the package from `infra/` into the backend environment or run from
`infra/`. Catch `ValidationError` using Member 2's standard error handling.
Authentication, facility-level access, and trusted snapshot creation remain
backend responsibilities. Do not allow browser-supplied stock/policy values to
be treated as authoritative.

## Snapshot shape

```json
{
  "request_id": "request-001",
  "inventory_snapshot_id": "snapshot-001",
  "captured_at": "2026-09-30T11:59:00Z",
  "destination": {"id": "destination", "active": true},
  "medicine": {"id": "med", "unit": "tablet"},
  "required_quantity": 1000,
  "sources": [{
    "facility": {"id": "source", "active": true},
    "inventory_complete": true,
    "selected_batch_id": "batch-a",
    "safety_stock": 300,
    "reserved_quantities": {"row-a": 100},
    "distance_km": 10,
    "transport_cost_per_unit_paise": 5,
    "inventory": [{
      "id": "row-a", "facility_id": "source", "batch_id": "batch-a", "quantity": 800,
      "batch": {"id": "batch-a", "medicine_id": "med", "expires_on": "2026-12-01", "recalled": false}
    }]
  }]
}
```

The timestamp above is illustrative. Real calls require a fresh capture time;
default maximum age is 300 seconds. Future and timezone-less timestamps fail.
`now=` exists for deterministic tests; production calls should use the server
clock. Shelf life is computed using the current UTC date, including midnight
rollover since capture.

## Inputs that Member 2 must supply explicitly

The inspected backend has no safety-stock, reservations, location, transport
cost, recommendation persistence, or transfer approval models yet. Therefore:

- Supply safety stock for the requested medicine/unit and source facility.
- Supply reserved quantities keyed by every inventory row ID. Explicit zero is
  permitted only when the backend knows that no reservation exists.
- Supply distance and marginal per-unit transport costs; never a fixed trip quote.
- Select one batch per facility for this restricted optimizer.
- Fetch all relevant inventory pages and capture a consistent snapshot. Setting
  `inventory_complete` to true is an assertion, not a completeness proof. Merely
  concatenating pages while stock is changing does not ensure consistency.

For each source, eligible stock excludes inactive facilities, recalled batches,
other medicines, and insufficient shelf life. Reservations are subtracted before
computing total available stock. Transferable quantity is:

```text
min(selected batch available, max(0, total eligible unreserved stock - safety stock))
```

Other eligible batches contribute to retained stock but are not transferred by
this version. Thus unresolved demand may remain even when other batches could
satisfy it. Results include `surplus_calculations` and `snapshot_exclusions` to
make these decisions reviewable. Matching medicine IDs assumes the backend
catalog accurately distinguishes strength/formulation; storage and transport
compatibility must still be checked by the backend.

## Remaining integration work owned by the backend

1. Add a permission-protected recommendation route using existing auth patterns.
2. Read trusted inventory/policy in a consistent database snapshot.
3. Persist recommendation ID, input version, result, expiry, and actor audit data.
4. Handle retries/idempotency and an authorized approval/rejection workflow.
5. At approval, atomically recheck stock, recall/expiry, safety stock, reservations,
   and permissions; reserve quantities before scheduling transfers.

Do not call the existing inventory issue endpoint to simulate approval: it
deducts stock and does not implement a transfer approval/reservation lifecycle.

## Targeted verification

From `infra/`:

```powershell
python -m unittest optimization.tests.test_backend_adapter -v
```

No backend server, database, Docker service, or network connection is needed.
