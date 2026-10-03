# Phase 5 — final integration and readiness audit

Completed: 2026-10-03 (Asia/Calcutta); full-suite/live evidence recorded 2026-10-02.
Branch: `integration/frontend-backend`. Starting HEAD: `4cd00a4`.

**Status: VERIFIED for the supported local integration and team review. Not staging-certified.**
This conclusion includes real PostgreSQL mutations, rejected writes, actual queued
Celery execution and clean frontend installation/build, not just unit-test results.
No commit, push, merge, deployment, persistent-database reset, administrator password
reset, Docker-container recreation or volume deletion was performed.

Continuation inspection: steps 1-14 were COMPLETE except the final configuration
review; documentation/report (15-16) and final Git inventory (17) were PARTIAL.
No phase was NOT STARTED. Saved evidence already contained 87 backend passes and
129 frontend passes, beyond the earlier 86/128 checkpoint. Only the remaining
configuration guard, focused validation, report inventory and final review were completed.
Verification labels: **VERIFIED** means actually executed or inspected as specified;
**UNVERIFIED** includes real-browser and remote-CI execution; **UNSUPPORTED** means
no functional UI claim; **EXTERNAL/INFRASTRUCTURE** identifies provider/server dependencies.

## 1. Scope and preservation

The complete Phase 1–4 working tree was inspected and fingerprinted before editing.
Existing authentication, permission boundaries, read integrations and mutation workflows
were preserved. `frontend/package-lock.json` is byte-identical to the Phase 5 baseline;
its pre-existing Git diff removes 42 lines of optional-package `libc` metadata.
That diff belongs to the existing working tree, not this audit.

Phase 3 coverage remains **33 frontend areas**; combined coverage remains **84/125 API
operations**. Phase 4 remains **77 workflow dispositions**, **169 control declarations**,
**48 connected actions / 32 endpoint families**, **13 read-only families**, and
**16 unsupported/deferred families**. No unused API was exposed just to raise coverage.

Only these hardening changes were made in Phase 5:

- Optional report-job request idempotency, using existing mutation receipts and an
  actor-row lock; current authorization is checked before replay. No migration needed.
- Frontend report requests retain their key across uncertain retries/remounts.
- Production frontend builds require an explicit API URL; development retains its
  documented localhost default. The client has no production localhost fallback.
- Production backend startup requires explicitly supplied database/Redis URLs,
  frontend/backend URLs and CORS origins; implicit development defaults are rejected.
  Explicit loopback URLs remain permitted for deliberate local production-mode probes.
- Broader private-env, coverage and Beat-state ignores; verified `.env.example` remains visible.
- Backend Makefile/CI commands verify/use `.venv`; frontend CI uses `npm ci`, runs
  tests, and supplies an explicit same-origin build URL. No lockfile fallback install.
- Focused concurrency/retry/timeout tests and portable live-test Python paths. Live
  receipts reuse the existing batch expiry instead of assuming fixtures were created today.
- A guarded, reproducible disposable-database/worker/Beat probe and corrected setup docs.

## 2. Configuration, secrets and reproducibility

Private development/verification environment files and fixture credentials were read
without printing their values. Changed text was checked against configured private
passwords, signing secrets and credential URLs, plus JWT/private-key/AWS-key patterns:
**no matches found**. Literal unit-test credentials are confined to isolated fixtures;
they are not deployed account credentials. No private environment file is tracked or staged.
Machine-specific paths were removed from executable setup examples; live probes resolve
the checkout and choose Windows/POSIX `.venv` executables.

Ignored: `.env`, `.env.*` except `.env.example`, `.venv`, `node_modules`, `dist`,
`coverage`, Python/pytest caches, SQLite databases, logs, `tmp/`, and Beat schedule files.
Generated OpenAPI evidence, JUnit/Vitest results, fixture ownership manifests, private
account records, isolated npm installation and worker logs remain under ignored `tmp/`.
Generated selected request schemas and TypeScript API types are intentional source files.

Use [DEVELOPMENT.md](DEVELOPMENT.md) for exact setup, migration, bootstrap, startup,
worker, Beat, test and shutdown commands. Required settings are documented in
`backend/.env.example` and `frontend/.env.example`: database credentials/URL, Redis URL,
JWT secret, frontend/backend URLs and explicit CORS origins. `JWT_REFRESH_SECRET` is
reserved; typed access/refresh JWTs use `JWT_SECRET` plus persistent session validation.
Optional weather/provider and disposable-test variables are documented separately.

An isolated frontend copy under `tmp/phase5-clean-frontend` successfully ran
**`npm ci --offline` and `npm run build`** from the preserved lockfile, with no private
environment files and explicit `VITE_BACKEND_URL=/`. A second build without that
variable failed with the intended configuration error. The original dependencies
and lockfile were untouched. No new Python packages were installed; the existing
`backend/.venv` passed `python -m pip check`. A fresh Python dependency installation
was not repeated; requirements are version ranges rather than an exact Python lock.
Fresh database migration and production-mode API startup were executed independently.

The root `docker-compose.yml` and root Compose Make targets are **legacy scaffolding**,
not a supported integrated quickstart or staging manifest: plain PostgreSQL lacks the
required PostGIS package, JWT/CORS forwarding is incomplete, and worker/Beat deployment
is absent. The supported local path explicitly uses `backend/compose.dev.yml` and
foreground backend/frontend/worker commands. No existing container or volume was replaced.

## 3. Infrastructure and migrations

| Check | Measured result |
|---|---|
| Persistent DB identity | `sanjeevani_dev`, port 5432; preserved |
| Verification DB | `sanjeevani_test`, port 55432; tests create/drop UUID schemas only |
| PostgreSQL / PostGIS | 16.9 / 3.5.2; both Compose projects healthy |
| Redis | 7.4.11; development 6379, disposable verification 16379/database 15; PING passed |
| Alembic | One head, current `c83d9e124a35`; `alembic check`: no new upgrade operations |
| Empty database | Generated `phase5_*_test`; upgrade head and drift check passed |
| Round trip | Disposable head → downgrade one → upgrade head; seeded facility preserved; drift clean |
| PostGIS ownership filter | Real application drift remains detectable, including app-owned `spatial_ref_sys` |
| Constraints | Real PG concurrency, immutable ledger/audit and PostGIS distance/index tests passed |
| API/frontend | Health and Vite HTTP 200; current live OpenAPI equals imported app schema |
| CORS | Both localhost and 127.0.0.1:5173 origins pass authenticated POST preflight; untrusted origin denied |

The final migration is a warehouse-active-state data correction; its downgrade
deliberately does not reconstruct old inconsistencies. The round trip proves only
the tested final revision, not arbitrary data-reversibility of the entire history.
The persistent development database was never downgraded. The generated worker-test
database was dropped after verification; no development/test Compose volume was deleted.

Runtime measured: Python 3.11.9, FastAPI 0.141.1, SQLAlchemy 2.1.1, Alembic 1.20.0,
Celery 5.6.3, redis-py 5.3.1, pytest 8.4.2, Node 24.14.0, npm 11.9.0.
CI's Linux/Node 20/Python 3.12 jobs have not been run remotely by this audit.

## 4. Contract and authorization

Live OpenAPI contains **125 operations across 101 paths**. All **84 covered operations**
still exist with the expected methods. All **32 selected frontend mutation request
schemas** match live OpenAPI exactly, including `ReportJobRequest`. No stale endpoint
was found. The matrices retain the method/path, permission, state and coverage inventory;
their historical report-job idempotency notes are superseded by this audit.

Contract checks include form-encoded `POST /api/v1/auth/login` (bare token pair),
`GET /api/v1/users/me`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`,
JSON mutation envelopes, strict request validation, binary report downloads,
query/path parameter use and current response models. HTTP 401 ends/refreshes the
session appropriately; 403 is permission denial; scoped 404 intentionally conceals
inaccessible facilities; 409 reflects state/idempotency conflicts; 422 is validation;
500/503 produce an unavailable state, never a fake successful response.

Real login/JWT/profile/protected read/refresh/logout and former-demo-credential rejection
passed through React and actual HTTP. PostgreSQL-backed tests verify read-only mutation
denial, wrong-facility denial and invalid-session rejection. The isolated worker probe
also exercised production-mode HTTP login/refresh/logout using Redis and fresh PostgreSQL.
Backend authorization remains authoritative; frontend role labels do not grant permissions.

Preserved permission/contract mismatches:

- Facility/geography directory reads still require `inventory.read`. Narrow beds,
  workforce and equipment users do not gain that permission. Their frontend uses
  authorized facility IDs/manual UUID selection or an honest unavailable directory;
  the backend checks actual facility scope on the operation.
- Transfer cancellation/receipt controls require readable linked-shipment state
  (`procurement.read`) to determine eligibility. Missing capability hides/disables the
  relevant action rather than guessing that no shipment exists. Backend transfer and
  shipment state machines remain unchanged.
- Async report jobs accept facility/kind/format, not all interactive report-page filters;
  the UI states this. Jobs are bounded to 500 rows, owned, authorized at generation and
  retrieval, and expire; new submissions are not evidence of completion.

## 5. Live read and mutation evidence

Opt-in run: **12 passed, 1 skipped**: two authentication tests, five read tests and five
mutation tests. The skipped outage-only case was then run separately: **1 passed,
2 skipped** (the two normal-auth cases intentionally disabled in outage mode).
Thus all 13 distinct opt-in cases ran successfully across the two configurations.

| Real path | Result |
|---|---|
| Facilities, inventory, expiry/safety, beds, alerts, suppliers/procurement, reports | PostgreSQL → FastAPI → authenticated client → React rendering passed |
| Backend bed change → frontend refresh | SQL change observed in React, then original occupancy restored |
| Inventory receive/issue/adjust | React → HTTP → business rules → SQL quantities/ledger → refetch/render passed |
| Transfer create/approve/dispatch/transit/receive | SQL source decreased 5 and destination increased 5; UI reached received |
| Alert acknowledge/resolve | Real persisted statuses and refreshed incident UI passed |
| Beds | Real capacity/occupancy update and UI restoration passed |
| Report request/poll/download | Pending job persisted, generated bytes downloaded, completed UI rendered |
| Rejected stock issue | API 409 and independent PostgreSQL before/after snapshot identical |

The live React tests use jsdom and real network requests, not a browser engine. The
shared test setup substitutes Leaflet; these checks do not claim interactive map/browser
verification. Actual computer-use initialization was attempted and failed before any
browser connection: Windows `CreateProcessWithLogonW` error 1056. Browser E2E remains unverified.

The live development report test invokes the guarded scoped generation helper after
creation; it does not claim worker execution. **Separate actual worker/Beat evidence
below closes that infrastructure gap.** No fallback mock data was used in live tests.

## 6. Report retry decision and background execution

Decision **A: fix uncertain retry reliability**, while preserving intentional independent
report snapshots. `POST /report-jobs` accepts optional `idempotency_key` (1–100 characters).
Same actor/key/body returns the original job; changed body with the same key returns 409.
No key or a new key intentionally creates a new snapshot. Authorization precedes replay;
job/receipt/audit commit together. Existing receipt storage means no new migration.
The UI generates and preserves the key for retries, including remount after a lost response.
There is still no job cancellation endpoint; the UI does not advertise cancellation.

`backend/scripts/verify_readiness_infrastructure.py` actually ran:

1. Fresh production-mode FastAPI with isolated PostgreSQL and Redis database 15.
2. Authenticated report creation over HTTP, plus identical keyed replay.
3. Celery worker (`solo`, one process, unique queue) consuming `reports.generate` from Redis.
4. Worker result `1`, persisted completed job, authenticated binary download.
5. A queued retry returning `0`, without regenerating an already completed job.
6. Separate Celery Beat publishing `reports.generate` every second on the unique queue;
   the second pending job completed through that worker.
7. Logout invalidation, worker/Beat/API termination and owned-database cleanup.

Production Beat's six registered schedules were inspected: report generation/scheduling/
expiry, alert dispatch/escalation and notification delivery. The controlled test overrides
only the interval/queue for report generation. It does **not** certify external notification
providers or every periodic task. No unattended production worker deployment is claimed.

Concurrency evidence: competing PG stock writers cannot overspend stock; concurrent
transfer dispatch gives one success/one 409 and exactly one outgoing ledger entry;
concurrent same-key report creation gives one job/audit; concurrent report generation
completes once. Frontend tests cover synchronous double-submit prevention and stable
retry payloads. Transfer state actions intentionally reject repeated transitions rather
than returning a replay success; they do not duplicate stock effects.

## 7. Outages, fixtures and tests

Actual unavailable backend transport produced a visible React login error with no session.
An isolated process connecting to an unreachable PostgreSQL port returned sanitized 503.
The real Redis test used a deliberately invalid Redis DB index in production mode and
verified `AUTH_UNAVAILABLE` 503; no shared Redis service was stopped. The test also checks
actual Redis limiter counters/expiry. A timer regression verifies the client's 15-second
abort and no invented session. HTTP 400/401/403/404/409/422/429/500/503 UI cases pass.

`DEV-PHASE3` and the existing `DEV-P4-*` manifest-owned records are DEVELOPMENT ONLY
verification fixtures. They remain isolated from other data. Phase 5 reused them: accepted
stock/transfer mutations intentionally leave audited test ledger entries, report artifacts
and resolved alert history; bed occupancy is restored. No blind cleanup or password reset.
Application startup has no dependency on those records. Guarded seed/verification scripts
refuse the wrong database; fixture manifests remain private under `tmp/`. The ordinary
bootstrap and real UI provide a supported setup without test fixtures.

| Final check | Exact result |
|---|---|
| Backend full suite with disposable PG/PostGIS/Redis enabled | **87 passed, 1 skipped, 1 warning**, 109.65 s |
| Final focused backend checks after production configuration guard | **14 passed**, 15.42 s; startup, authentication, PG concurrency/drift/scope and Redis |
| Backend skip | TimescaleDB requires `ENABLE_TIMESCALEDB=1` and compatible TimescaleDB/PostGIS server |
| Frontend full suite | **129 passed, 13 opt-in skips**, 0 failures |
| Separate live normal run | **12 passed, 1 outage-mode skip**, 0 failures |
| Separate live outage run | **1 passed, 2 normal-mode skips**, 0 failures |
| Production frontend build | Passed; 2396 modules; JS 1031.05 kB / gzip 298.01 kB |
| Isolated offline lockfile install/build | Both passed |
| Missing API URL negative build check | Correctly rejected |
| Import/lifespan/OpenAPI | Passed; live/imported schema identical |
| Alembic heads/current/check | Single current head; no drift |
| Git whitespace | Passed; line-ending notices only |

Commands: activated backend `.venv`, load private `.env.local`, then
`python -m pytest -q -rs --tb=short --junitxml=../tmp/phase5-backend.xml`;
frontend `npm test -- --reporter=json --outputFile=../tmp/phase5-frontend.json`,
`npm run build`. The full backend suite preceded the final production-only configuration guard;
14 focused checks passed afterward. A broad rerun was not necessary because routes,
schemas, persistence and development-mode behavior were unchanged by that guard.
The frontend suite/build were rerun after the last frontend source/test change.
No tests were weakened. Detailed private evidence is in `tmp/phase5-*`; checked-in
regressions and guarded scripts permit repetition without committing private logs.

The first continuation targeted attempt recorded 9 passes, 4 setup errors and 1 Redis
failure because Docker Desktop was stopped (connection refused). The five new startup
checks passed in that attempt. Starting Docker Desktop restored the existing four
containers without recreation; the same complete targeted selection then passed 14/14.
This failed infrastructure attempt is retained here rather than hidden. No completed
live chain, frontend suite, build or worker probe was rerun merely for this continuation.

## 8. Remaining issue classification

| Issue | Classification | Effect / required action |
|---|---|---|
| Supported local integration correctness/security/data integrity | **No known BLOCKER** | Representative real flows and failure paths verified |
| Staging deployment configuration | **SHOULD FIX BEFORE STAGING** | Supply reviewed deployment manifest, explicit build/runtime origins, secret injection, TLS/proxy configuration, least-privileged runtime DB role, supervised worker and single Beat; exercise staging migrations and backup/restore |
| Actual browser E2E | **SHOULD FIX BEFORE STAGING** | Tool initialization blocked; validate browser login, CORS, routing, controls and downloads on target host |
| Remote CI/team review | **BLOCKER for merge approval only** | No remote CI or team review was executed; do not merge before both approve this exact diff |
| Python dependency ranges | **SHOULD FIX BEFORE STAGING** | Capture approved resolved dependencies/build image for reproducible deployment; current venv pip check and suite pass |
| TimescaleDB-specific test | **ACCEPTABLE LIMITATION** | Optional server unavailable; ordinary PG/PostGIS cold-chain behavior works; do not claim hypertable verification |
| Weather provider | **ACCEPTABLE LIMITATION** | Unconfigured; actual endpoint returns 503 and UI shows unavailable; configure only when this optional feature is required |
| Bundle warning >500 kB | **ACCEPTABLE LIMITATION** | Production build passes; optimize/split if target-device performance requires it |
| Starlette/httpx test deprecation | **ACCEPTABLE LIMITATION** | One warning, no failed tests; dependency migration can be planned separately |
| Git LF/CRLF notices | **ACCEPTABLE LIMITATION** | No whitespace errors; existing Windows checkout behavior |
| Independent report snapshots | **ACCEPTABLE LIMITATION / intentional semantics** | New key/no key makes a new snapshot; uncertain keyed retries are fixed |
| Celery worker/Beat | **Verified locally** | Real queued execution passed; supervised staging topology still required |
| 33 non-GET and 8 GET operations without UI coverage | **INTENTIONALLY UNSUPPORTED in UI** | Existing backend capability does not imply a legitimate frontend action; see matrix |
| Read-only administration, account provisioning UI | **INTENTIONALLY UNSUPPORTED** | Governed backend/bootstrap remain; no fake management success |
| Prediction probabilities, oxygen runway, outbreak polygons, optimizer promises | **INTENTIONALLY UNSUPPORTED** | No matching integrated backend contract; unavailable rather than fabricated |
| Federated training UI | **INTENTIONALLY UNSUPPORTED** | No claimed end-to-end model workflow |
| Offline mutation synchronization | **INTENTIONALLY UNSUPPORTED in UI** | Connectivity state only; no fabricated queued success |
| Camera scanning | **INTENTIONALLY UNSUPPORTED** | Registered barcode text lookup works; optical scanner not connected |
| External notifications/FHIR/HL7/provider deployment | **ACCEPTABLE LIMITATION / external dependency** | Internal contracts do not prove external delivery/interoperability; configure and test providers before relying on them |
| Facility/geography permission mismatch | **ACCEPTABLE LIMITATION** | Manual/assigned IDs and unavailable directories preserve RBAC; no inventory grants added |
| Transfer shipment-read prerequisite | **ACCEPTABLE LIMITATION** | Controls conservatively require known shipment state; backend is authoritative |

Unused backend operations remain enumerated in
[PHASE4_MUTATION_MATRIX.md](frontend/PHASE4_MUTATION_MATRIX.md) and
[API_INTEGRATION_MATRIX.md](frontend/API_INTEGRATION_MATRIX.md). No API coverage count
was raised by adding unsupported workflows.

## 9. Readiness decisions and recommended Git boundary

- **A. Safe to commit: YES**, the reviewed integration source/docs/tests below.
- **B. Safe to push integration branch for team review: YES**; do not treat this as deployment approval.
- **C. Safe to merge into develop now: NO**; exact remaining gate is successful remote
  CI on the proposed commit and team review. These have not run. No known local technical blocker remains.
- **D. Ready for staging deployment now: NO**; the staging configuration and actual
  browser verification listed above are not supplied/verified. The legacy root stack
  must not be presented as a staging-ready manifest.

Recommended boundary: one coherent Phase 1–5 integration commit containing the exact
inventory below **except `frontend/package-lock.json`**, which is preserved pre-existing
user work and should remain unstaged unless its owner explicitly elects to include it.
Do not stage private configuration, verification logs, databases, fixtures or builds.
Review the lockfile diff separately; the isolated install check used its current contents.

Recommended next steps (not executed): inspect `git diff`, review every new file below,
stage only approved inventory paths, run `git diff --cached --check` and
`git diff --cached --name-status`, then commit with message
`Integrate authenticated frontend workflows and verify readiness`. Push only
`integration/frontend-backend` for review; wait for required CI and approvals before a
separate merge decision. Do not merge/deploy as part of this audit.

## 10. Exact changed-file inventory

The following 106 files are the complete current Git working-tree inventory, including preserved
Phase 1–4 files. `M` means tracked modification, `??` means new untracked source/document.
No files were staged by this audit.

```text
 M .github/workflows/backend-ci.yml
 M .github/workflows/frontend-ci.yml
 M .gitignore
 M Makefile
 M README.md
 M backend/INFRASTRUCTURE_VERIFICATION.md
 M backend/README.md
 M backend/alembic/env.py
 M backend/app/api/v1/endpoints/identity.py
 M backend/app/api/v1/endpoints/report_jobs.py
 M backend/app/core/database.py
 M backend/app/main.py
 M backend/app/schemas/outputs.py
 M backend/app/schemas/report_jobs.py
 M backend/app/services/identity.py
 M backend/app/services/report_jobs.py
 M frontend/package-lock.json
 M frontend/src/app/App.tsx
 M frontend/src/app/router.tsx
 M frontend/src/components/common/CommandPalette.tsx
 M frontend/src/components/common/OfflineIndicator.tsx
 M frontend/src/components/common/ProtectedRoute.tsx
 M frontend/src/components/common/RoleGuard.tsx
 M frontend/src/components/common/RoleSidebar.tsx
 M frontend/src/components/common/RoleTopBar.tsx
 M frontend/src/components/common/TopBar.tsx
 M frontend/src/modules/admin/AdminPage.tsx
 M frontend/src/modules/alerts/AlertsPage.tsx
 M frontend/src/modules/analytics/AIDashboard.tsx
 M frontend/src/modules/auth/ForgotPasswordPage.tsx
 M frontend/src/modules/auth/LoginPage.tsx
 M frontend/src/modules/auth/MFAPage.tsx
 M frontend/src/modules/auth/ProfilePage.tsx
 M frontend/src/modules/auth/RegisterPage.tsx
 M frontend/src/modules/auth/SettingsPage.tsx
 M frontend/src/modules/beds/BedsPage.tsx
 M frontend/src/modules/dashboard/DistrictDashboardPage.tsx
 M frontend/src/modules/dashboard/FacilityDashboardPage.tsx
 M frontend/src/modules/dashboard/NationalDashboardPage.tsx
 M frontend/src/modules/dashboard/RegionalDashboard.tsx
 M frontend/src/modules/dashboard/StateDashboardPage.tsx
 M frontend/src/modules/disease/DiseasePage.tsx
 M frontend/src/modules/emergency/EmergencyPage.tsx
 M frontend/src/modules/equipment/EquipmentPage.tsx
 M frontend/src/modules/facilities/FacilitiesPage.tsx
 M frontend/src/modules/facilities/WarehouseDashboardPage.tsx
 M frontend/src/modules/federated-ai/FederatedAIPage.tsx
 M frontend/src/modules/inventory/InventoryPage.tsx
 M frontend/src/modules/map/InteractiveResourceMap.tsx
 M frontend/src/modules/patients/PatientsPage.tsx
 M frontend/src/modules/workforce/WorkforcePage.tsx
 M frontend/src/pages/HomePage.tsx
 M frontend/src/services/api.ts
 M frontend/src/services/authService.ts
 M frontend/src/store/authStore.ts
 M frontend/src/test/authRoleRouting.test.tsx
 M frontend/src/test/blueprintPhases.test.tsx
 M frontend/src/test/member1Deliverables.test.tsx
 M frontend/src/types/auth.ts
 M frontend/vite.config.ts
?? DEVELOPMENT.md
?? FINAL_READINESS_AUDIT.md
?? backend/.env.example
?? backend/DEVELOPMENT_ENV_VERIFICATION.md
?? backend/app/core/migration_filters.py
?? backend/compose.dev.yml
?? backend/scripts/seed_phase3_development.py
?? backend/scripts/verify_phase3_frontend.py
?? backend/scripts/verify_phase4_data.py
?? backend/scripts/verify_phase4_frontend.py
?? backend/scripts/verify_readiness_infrastructure.py
?? backend/tests/test_frontend_auth_contract.py
?? backend/tests/test_infrastructure_integration.py
?? backend/tests/test_phase4_mutations.py
?? backend/tests/test_readiness.py
?? frontend/.env.example
?? frontend/API_INTEGRATION_MATRIX.md
?? frontend/AUTH_INTEGRATION.md
?? frontend/PHASE3_DATA_INTEGRATION.md
?? frontend/PHASE4_MUTATION_MATRIX.md
?? frontend/PHASE4_OPERATIONAL_INTEGRATION.md
?? frontend/src/app/authorization.ts
?? frontend/src/components/common/BackendData.tsx
?? frontend/src/components/common/FacilityPicker.tsx
?? frontend/src/components/common/MutationForm.tsx
?? frontend/src/hooks/useBackendData.ts
?? frontend/src/hooks/useFacilityDirectory.ts
?? frontend/src/modules/analytics/OperationalContext.tsx
?? frontend/src/modules/analytics/ReportsPanel.tsx
?? frontend/src/modules/dashboard/BackendDashboard.tsx
?? frontend/src/modules/equipment/OperationsActions.tsx
?? frontend/src/modules/facilities/FacilityActions.tsx
?? frontend/src/modules/facilities/SupplyActions.tsx
?? frontend/src/modules/inventory/BatchTracePanel.tsx
?? frontend/src/modules/inventory/ColdChainPanel.tsx
?? frontend/src/modules/inventory/InventoryActions.tsx
?? frontend/src/services/backendTypes.ts
?? frontend/src/services/dataApi.ts
?? frontend/src/services/httpClient.ts
?? frontend/src/services/mutationSchemas.ts
?? frontend/src/test/authLive.integration.test.tsx
?? frontend/src/test/dataIntegration.test.tsx
?? frontend/src/test/dataLive.integration.test.tsx
?? frontend/src/test/dataTestUtils.tsx
?? frontend/src/test/mutations.test.tsx
?? frontend/src/test/mutationsLive.integration.test.tsx
```

