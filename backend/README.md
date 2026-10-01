# Sanjeevani Member 2 backend

The backend extends the original FastAPI foundation. It includes authentication,
scoped RBAC, geography, inventory, redistribution, supply-chain operations, beds,
workforce, operational aggregates, alerts, reports and integration boundaries.
Read [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for phase status and
[IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) for the generated handoff inventory.
Local tests do not establish production readiness: PostgreSQL/PostGIS and Redis
must be provisioned and exercised before deployment.

## Environment and dependencies

All project Python dependencies belong in `backend/.venv`. Nothing is installed globally.
From the repository root, create the environment if it is missing:

```bat
python -m venv backend/.venv
call backend\.venv\Scripts\activate.bat
python -c "import sys; from pathlib import Path; assert sys.prefix != sys.base_prefix; assert Path(sys.prefix).resolve() == Path('backend/.venv').resolve(); print(sys.executable)"
python -m pip install -r backend\requirements.txt
cd backend
```

Use Command Prompt activation if PowerShell execution policy blocks Activate.ps1.
Run backend commands from `backend`. Settings read `backend/.env`; Compose reads
root `.env`. Both files, `.venv`, bytecode and local test databases are ignored.
The root `.env.example` contains variable names only. Empty entries are ignored by
backend settings. Supply real values in untracked environment files/secret storage.

| Variable | Purpose |
|---|---|
| APP_ENV | development, testing or production; use production for deployed servers |
| DATABASE_URL | PostgreSQL URL using the asyncpg SQLAlchemy driver |
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | Local fallback database settings and Compose configuration |
| JWT_SECRET | Random signing secret, at least 32 characters |
| REDIS_URL | Celery broker/result backend and production authentication rate-limit store |
| BACKEND_CORS_ORIGINS | JSON array of explicit allowed browser origins |
| AUTH_RATE_LIMIT / AUTH_RATE_WINDOW_SECONDS | Authentication request limits per client address/route |
| WEATHER_PROVIDER | Set to open-meteo to enable the implemented public weather adapter |
| WEATHER_CACHE_SECONDS | Weather cache lifetime |
| BACKUP_RETENTION_DAYS / BACKUP_MAX_AGE_HOURS | Infrastructure retention contract and metadata health threshold |
| BACKUP_STORAGE_NAME | Non-secret label for infrastructure-managed backup storage |
| TEST_DATABASE_URL | Opt-in disposable PostgreSQL/PostGIS test database, name ending `_test` |

The inherited JWT_REFRESH_SECRET and WEATHER_API_KEY names are retained for team
compatibility. Current refresh tokens use typed JWTs signed with JWT_SECRET and
persistent hashed session tokens. The implemented public Open-Meteo adapter does
not require a key. Other inherited AI/frontend environment variables are unchanged.
Generate a signing secret locally with:

```bat
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Production startup requires PostgreSQL, JWT_SECRET, Redis configuration and explicit
CORS origins. Production authentication fails closed if its Redis limiter is unavailable.
Development uses an in-process limiter; `testing` bypasses it for isolated fixtures.
Only use `testing` in tests. Configure trusted proxy addresses at ASGI deployment;
the limiter does not trust arbitrary forwarding headers.

## PostgreSQL, PostGIS and migrations

Provision a PostgreSQL database and a role with migration permissions. Install the
PostGIS package on the database server first. The security migration enables the
extension and builds the facility geography index. A database administrator may
pre-create PostGIS when the application migration role lacks extension privileges.
PostgreSQL migrations add immutable-ledger triggers for stock transactions and audit logs.
Runtime database credentials should have only the privileges needed by the application.

```bat
python -m alembic heads
python -m alembic upgrade head
python -m alembic check
python -m app.bootstrap
python -m uvicorn app.main:app --reload
```

Bootstrap prompts for an administrator username/password; there are no default accounts.
Existing users with the original `administrator` role receive the expanded capability
catalogue and global scope through migration. Other existing users become restricted
and need explicit facility/district assignments. No migration is applied automatically
at application startup. Preserve the existing migration chain; do not edit deployed revisions.

Temperature observations have indexed UTC timestamps. TimescaleDB is deliberately
not enabled without measured volume/retention requirements. A future hypertable
conversion needs a reviewed migration accounting for time-partitioned unique keys.

## API and authentication

Swagger: `/api/v1/docs`; OpenAPI: `/api/v1/openapi.json`.
New endpoints use `{ "success": true, "data": ... }`; handled errors use
`{ "success": false, "error": { "code": ..., "message": ... } }`.
The existing root/health responses and OAuth2 login response remain compatible.
Login accepts OAuth2 form fields and returns access_token, token_type, expires_in
plus refresh_token. `/auth/refresh` accepts JSON refresh_token and returns an envelope.

Access tokens expire after 15 minutes. Refresh sessions last seven days, rotate on
use and store hashes only. Replaying a consumed refresh token revokes its session
family. Logout revokes all account sessions. Password changes/resets invalidate
sessions; reset tokens are single-use, hashed and short-lived. Recovery responses
are identical for unknown accounts and delivery failures. Passwords and token values
are not recorded in audit metadata.

`/users/me` and existing `/auth/me` expose safe profiles. `admin.users` and global
scope gate user, role and permission administration. New accounts default to
restricted scope. Facility grants and dynamic district grants control object access.
Role names supplied by clients never grant authority by themselves. Self-removal of
administrative access is rejected. MFA and recovery use bounded provider hooks in
`app/integrations/identity.py`; required MFA fails closed. Trusted recovery-address
lookup, enrollment and live delivery providers must be configured externally.

## Inventory and redistribution

1. Create a facility and medicine through `/facilities` and `/medicines`.
2. Receive stock through `/inventory/receive` with facility_id, medicine_id,
   batch_number, expires_on, positive quantity and reference.
3. Issue through `/inventory/issue` with facility_id, medicine_id, quantity and reference.
4. Inspect `/inventory`, `/inventory/transactions`, `/inventory/expiry` and batch trace.

Receive/issue accept optional idempotency_key to preserve existing callers. New
adjustments, transfer requests and procurement receipts require retry keys. Matching
actor/operation/key/input replays a committed response; conflicting input returns 409.
Clients using legacy writes without keys retain the original non-idempotent behavior.

FEFO uses the earliest expiry, excluding recalled batches and batches expiring today
or earlier by UTC date. Adjustments are signed ledger deltas. RETURN adds stock;
DAMAGE, EXPIRED and RECALL remove stock with type-specific validation. Inventory,
ledger and audit changes commit or roll back together before sending the response.

Stock policies configure safety stock, critical/low DOS thresholds, minimum history,
lead time and expiry warning periods. DOS derives consumption from actual issue
transactions and distinguishes no history, insufficient history and zero consumption.
Unknown DOS/reorder values are null. Transferable stock excludes reservations and
safety stock. Recalls immediately prevent dispensing; resolving a recall records
its disposition without releasing the batch for issue.

Transfers progress pending_approval -> approved/rejected -> dispatched -> in_transit
-> received. Receipt may follow dispatch directly. Pending/approved transfers may
be cancelled. Approval reserves stock; dispatch posts TRANSFER_OUT; receipt posts
TRANSFER_IN. Both facilities must be in scope. Duplicate/invalid transitions return
409. Recalled/expired in-transit goods can be physically received but remain unusable.
All stock writers lock facilities in UUID order, then medicines in UUID order.

## Geography, supply chain and operations

Geography is normalized as countries -> states -> districts -> blocks -> facilities.
Facility updates support paired coordinates, address/contact, type and activation.
Search/filter by geography and scoped nearby queries are available. PostgreSQL uses
PostGIS geography distances; SQLite uses a spherical approximation for local tests.

Suppliers have editable contact/lead-time metadata; metrics derive from real orders
and shipment timestamps. Warehouses link to facilities and share the batch ledger.
Their inventory table references ledger-backed inventory instead of duplicating quantities.
Warehouse-to-facility movement uses transfers. Purchase orders progress through
submit/approve/order and partial/full receipts. Approval requires procurement.approve;
receiving also requires inventory.write. Shipment arrival does not automatically post
stock; receipt is a separate, audited operation. Shipment status history is preserved.

Cold-chain ingestion records timestamped source events and validated ranges; conflicting
retries are rejected. Trusted sensors/operators supply observations, never simulated data.
Bed capacity validates occupied <= capacity and retains occupancy snapshots. Staff
roles, facility assignments, non-overlapping shifts, cancellation and daily attendance
are supported. Footfall/disease counts are aggregates without patient-level identifiers.
Equipment maintenance preserves history. Ambulances store operator/provider-supplied
availability and optional coordinates; a tracking provider interface is included.

## Alerts, notifications and background work

Rules cover low/critical usable stock quantity, expiry windows, bed occupancy ratios,
scheduled staff shortages, maintenance and cold-chain excursions. Active alerts are
deduplicated by rule/source. Acknowledgment and resolution are explicit. Resolution
allows a still-present condition to alert again. Escalation rules can be created,
edited/disabled and inspected, with immutable escalation history.

Notification logs track attempts and safe failure codes. In-app notifications need
no external provider. Email/SMS/push providers must be registered; unconfigured
providers fail explicitly. Providers receive idempotency keys and must honor them.
Retries recheck recipient access. External delivery is at-least-once unless the
provider honors its idempotency contract. Failed notifications can be explicitly retried.

Set REDIS_URL and run workers and exactly one scheduler:

```bat
python -m celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo
python -m celery -A app.tasks.celery_app:celery_app beat --loglevel=info
```

The solo pool is for Windows development. Production worker deployment belongs to
Member 4. Periodic tasks dispatch alert checks, escalation, notification delivery,
report schedules/generation and expired artifact cleanup.

## Reports, export and audit

`/reports/{stock|expiry|transfers|procurement|staff|beds|emergency}` uses actual data.
Emergency reports currently mean critical alerts, not a separate incident registry.
Filters include facility, creation-date range (end exclusive), district/state and
supported medicine/status filters. JSON and CSV/XLSX/PDF exports are bounded to
500 records per request. Export requires reports.export; staff reports also require
workforce.read. X-Has-More and X-Next-Offset expose pagination. CSV/XLSX neutralize
formula-like text. PDF wraps record fields and preserves unsupported glyphs as
Unicode escapes. Rendering runs off the event loop.

`/report-jobs` queues bounded background exports; `/report-schedules` repeats them.
Workers and downloads recheck authorization. Background transfer snapshots require
global scope because they contain two-facility records. Oversized background reports
fail with an explicit code and direct clients to paginated exports. Artifacts expire
after one day; cleanup clears content while retaining job metadata/audit history.
Audit records carry correlation IDs. `/audit-logs` requires a global audit reader;
there are no audit-update/delete APIs.

## Offline sync

Push supports footfall and disease aggregates only. Every batch has an idempotency
key. expected_version=0 creates; updates must match the stored version. Any conflict
rolls back the entire batch. Clients fetch/reconcile and retry with a new key/version.
Inventory balances cannot be overwritten through sync.
Pull uses commit-ordered change sequences. Start with `after_sequence=0`; preserve
`until_sequence` from `next_cursor` while paging. After the final page, save the
integer `watermark` as the next `after_sequence`. Each immutable item includes
`change_sequence`. Keep independent cursors for each kind and authorization scope;
bootstrap again after scope expansion. The deprecated `since` parameter is accepted
only for a safe full bootstrap; timestamp/UUID continuation is no longer supported.
Access is rechecked on every request. No hard-deletion/tombstone protocol is needed
for the current aggregate allowlist, which exposes no deletion endpoint.

## Integration boundaries

- FHIR: limited R4 [Location](https://hl7.org/fhir/R4/location.html) projection, not a
  FHIR server or full standards-conformance claim. HL7 is a routing/adapter protocol;
  sender-specific profiles must be agreed before enabling clinical message ingestion.
- Member 3: scoped medicine-consumption and aggregate datasets, maximum 365-day
  intervals; stock history is exposed through the scoped transaction ledger.
- Member 4: validated recommendations with model/source metadata; applying an approved
  recommendation creates a pending transfer and never bypasses stock approval.
- Weather: fixed Open-Meteo endpoint with its [documented variables](https://open-meteo.com/en/docs),
  timeouts, bounded transient retries/response size, validation and coordinate-aware cache.
  Unavailable/malformed providers return 503. Live calls were not used to populate test data.
- Population: validated district association, source URL, as-of/retrieval timestamps;
  official dataset acquisition is a provider interface. No demographic values are invented.
- Barcode: unique lookup for a medicine or batch; scanner UI is outside backend.
- Backup: metadata/retention/health contract only. See [BACKUP_RUNBOOK.md](BACKUP_RUNBOOK.md).

## Tests and verification

```bat
python -m pytest -q
python -m alembic heads
python -m alembic check
python -m compileall -q app
python -m pip check
```

Tests use isolated temporary SQLite databases and never the configured application DB.
They cover authentication/session replay/logout/reset, MFA hooks, scopes, stock integrity,
FEFO, adjustments, recalls, transfers, supply chain, operational records, alerts,
notifications, exports, sync, integrations, background reports, security and migrations.
Fresh-database migration tests and PostgreSQL offline SQL compilation are included.

For live PostgreSQL validation, explicitly set TEST_DATABASE_URL to a disposable
PostgreSQL database whose name ends `_test`, with PostGIS already installed. Tests
create a unique schema, apply the actual Alembic chain, test competing stock writers,
PostGIS distance and ledger immutability, then drop only that generated test schema.
ALEMBIC_TEST_SCHEMA is an internal guarded test variable, not a deployment setting.
Without TEST_DATABASE_URL those tests are skipped, not reported as passing.

No commit, push, merge, deployment, production migration, backup or restore is run
by this implementation. Review the handoff report and live-service verification
requirements before integration.

## Correctness contracts after the independent audit

All system-derived business dates use UTC, including maintenance, expiry and
consumption boundaries. Input calendar dates are ISO dates interpreted in that
UTC business calendar; do not derive them using a workstation's local date.

Transfers require active facilities for creation, approval and dispatch. Existing
transfers may be cancelled/rejected or received after deactivation, subject to the
same permissions, scopes and state checks. Cancellation releases reservations;
repeated terminal transitions return 409. Transfer approval enforces the sum of
requested batches against usable, unreserved medicine stock minus configured
safety stock. There is no implicit safety-stock override.

Purchase orders with non-cancelled shipments cannot be cancelled. Planned shipments
must be cancelled first; dispatched shipments must complete. A linked tracked
shipment must arrive before stock receipt. New shipments require ordered/partially
received POs or approved/dispatched/in-transit transfers. Transfer shipment movement
requires a dispatched/in-transit/received parent, and both facility scopes apply
to creation, list, history and actions.

Facility active state is authoritative for warehouses. Updates through either API
keep both flags aligned; warehouse facilities cannot change type through a generic
facility update. Existing mismatches are repaired by migration c83d9e124a35.
Resolved recall dispositions cannot be overwritten by repeated resolution calls.

Low/critical-stock evaluation includes policy-configured medicines even when no
inventory row exists. Expiry queries default to the medicine/facility policy window
(90 days without a policy); an explicit query `days` overrides the display window.
Expiry alerts use the policy window when present, otherwise the alert rule window.

Stock/expiry reports include medicine name/code/unit, batch number, expiry date,
facility name/code, quantity, reserved quantity, usable available quantity and
`expiry_state`. Expiry reports include expired and upcoming batches within policy
windows and accept `status=expired` or `status=upcoming`. Emergency reports mean
critical alerts, not an emergency incident registry. Date filters remain record
creation filters, not historical balance reconstruction.

Supplier `quantity_fulfilment_rate` replaces the misleading `quantity_accuracy`:
sum(received)/sum(ordered) for ordered, partially_received and received POs.
`fulfilment_rate` is fully received orders divided by that same eligible order set.
Draft/submitted/approved/cancelled POs are excluded; zero denominators yield null.
`order_count` counts all POs; `eligible_order_count` exposes the denominator.
Average delivery delay is mean(max(arrived_at - expected_at, 0)) in days over
arrived shipments with an expected time, so early arrivals do not offset late ones.

All JSON operations have explicit response models and error schemas. OAuth2 login,
root/health metadata, and CSV/PDF/XLSX download responses intentionally do not use
the standard success envelope. JSON extension payloads remain explicitly flexible.
The sync cursor and supplier metric changes require frontend/Member 3 coordination.

TimescaleDB support is opt-in during migration b72c8d013f24 using
`ENABLE_TIMESCALEDB=1` on a configured PostgreSQL/Timescale server. Cold-chain
samples have transactional ingestion and a scoped `/cold-chain/series` API.
SQLite uses the same ordinary table without an extension. See
[INFRASTRUCTURE_VERIFICATION.md](INFRASTRUCTURE_VERIFICATION.md) for the design,
maintenance-window requirements, exact Docker/PostGIS/Redis/Celery commands, and
the distinction between local verification and unexecuted infrastructure checks.
