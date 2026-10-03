> Current status: see [Phase 5 readiness audit](../FINAL_READINESS_AUDIT.md) and [supported setup](../DEVELOPMENT.md). This report retains historical phase results. Phase 5 adds optional report-job idempotency (`ReportJobRequest`), real Celery worker/Beat verification, and explicit production API configuration. Earlier statements about those gaps are superseded.

# Phase 4 operational integration report

Completed the scoped implementation and audit on `integration/frontend-backend`, 2026-10-02. Phases 1-3 and unrelated working-tree changes were preserved.

**Phase 4 status: PARTIAL.** The implemented operational controls and all five required representative live mutation chains are verified. The broader requirement for duplicate-safe operational submissions is not fully met by existing backend contracts: independent repeated report-job requests create separate jobs, and some event-creation APIs lack idempotency. Unattended report worker/beat execution was not verified. These gaps are explicitly documented rather than hidden by client success messages or new unsupported backend behavior.

**The project can proceed to the final integration/readiness audit with these limitations recorded.** That audit was not started, and this report does not certify deployment readiness.

## Audit and coverage

The [complete mutation matrix](PHASE4_MUTATION_MATRIX.md) provides every workflow's action, method, endpoint, permission/scope, exact request schema, success response, failure handling, state transition, idempotency, audit and refresh behavior. [API_INTEGRATION_MATRIX.md](API_INTEGRATION_MATRIX.md) retains the historical Phase 3 snapshot and adds current Phase 4 coverage.

| Measure | Result |
| --- | --- |
| Source control declarations audited | **169**, including buttons, forms, dropdowns, inputs, shared dialogs and mutation-form call sites |
| Action/workflow dispositions audited | **77** |
| Connected user actions | **48**, across **32 endpoint families** |
| Intentionally read-only workflow families | **13** |
| Unsupported/deferred families | **16**: 7 external/backend ingestion or execution boundaries and 9 unsupported UI action groups |
| Newly covered API operations | **31**; alert resolution shares the already covered alert-action endpoint |
| Combined frontend API coverage | **84/125** operations |
| Remaining uncovered API operations | **33 non-GET**, plus the previous **8 GET** operations |
| Representative live mutation chains executed | **5 passed**, covering **12 distinct action variants** |

Counting is explicit: individual connected transitions and geography levels are separate actions; related intentionally unexposed administrative endpoints are grouped into named workflow families. Source declarations, workflow dispositions and API operations are different measures. **48 connected controls does not mean 48 independently executed live workflows.** The five live chains supply the required representative end-to-end evidence; remaining controls rely on shared frontend regression coverage and backend business-rule tests.

Source-control classifications are 41 CONNECTED_MUTATION, 16 READ_ONLY_BY_DESIGN, 92 LOCAL_ONLY, 13 PLACEHOLDER, 6 NO_BACKEND_ENDPOINT and 1 DEFERRED_EXTERNAL_INTEGRATION. The 13 placeholder declarations are unreachable legacy `TopBar.tsx`/`HomePage.tsx` demonstrations. NOT_AUTHORIZED_FOR_ROLE is a runtime condition for connected controls with missing grants, scope or prerequisite access, rather than another duplicate source count.

## What changed

- Extended the existing authenticated data client to support DELETE alongside POST/PUT/PATCH. Concrete UI workflows use only methods their endpoints expose; no artificial delete control was added.
- Added schema-driven, labeled mutation forms using selected schemas exported from the actual running FastAPI OpenAPI document. Existing Cards, Modal, colors, tables and navigation were retained.
- Added local validation, backend-error display, synchronous submission locks, disabled pending controls, high-impact confirmation and real query invalidation. No optimistic stock balance or mock success is used.
- Connected inventory receive/issue/adjust, transfer lifecycle, supplier and warehouse metadata, procurement orders/receipts, shipment lifecycle, facility/geography administration, bed capacity, staff/roles/shifts/attendance, daily aggregates, equipment/maintenance and ambulance availability.
- Preserved real alert acknowledgement, added its immediate duplicate-click guard, and connected resolution. Manual escalation is not invented; escalation histories/rules remain readable.
- Connected report-job creation to actual status polling and completed downloads. `pending`, `completed`, `failed` and `expired` are the backend states. No fabricated RUNNING, cancellation or retry workflow is displayed.
- Added 30 frontend regression cases, five opt-in live mutation checks, three backend regressions, and guarded development verification scripts.

The two obsolete Phase 3 assertions were updated narrowly: the inventory test now permits real Receive stock controls while still rejecting fake dispensing/dispatch and asserting no POST occurs just from browsing; the unknown-barcode test now expects the backend's actionable `Unknown barcode` error and still verifies stale results disappear. Existing authentication assertions were preserved.

## Confirmed real mutation chains

`src/test/mutationsLive.integration.test.tsx` uses the actual React login form, real backend JWT, authenticated API client, running FastAPI and persistent PostgreSQL. It does not substitute mocked fetch responses, auth tokens or database state. Independent SQL probes verify the database separately from HTTP responses.

| Chain | Actual verification |
| --- | --- |
| Inventory | React receives 10 units, issues 4 through backend FEFO, and adjusts +1 on an isolated batch. SQL verifies each balance and three new ledger records; subsequent authenticated reads refresh the rendered table. Double-clicking the confirmation does not create a second action. |
| Transfer/supply chain | React creates a transfer, then approves, dispatches, marks in transit and receives it. SQL verifies source -5, destination +5 and received state; refetch updates the displayed lifecycle and removes invalid further receipt controls. Destination inventory HTTP agrees with PostgreSQL. |
| Alerts | React acknowledges the isolated open incident, then resolves it. SQL verifies acknowledged/resolved states and the actual incident card updates after refetch. Historical resolved records remain retained. |
| Operations/assets representative | React updates recorded beds, SQL confirms occupancy 4, and React renders 6 available. The `finally` cleanup restores the isolated bed through the same UI and confirms PostgreSQL restoration. Equipment/maintenance/ambulance forms have contract and backend regression coverage; their mutations were not separately live-certified. |
| Reports | React creates exactly one pending job, SQL identifies its new ID/status, and no completed-download control appears early. The existing report generator runs under a database guard that permits only that isolated pending job. SQL confirms completed content; frontend polling displays completion and real CSV bytes include the fixture medicine. This verifies the service and polling, **not unattended Celery worker/beat scheduling**. |

The transfer chain is the live supply-chain representative. Supplier edits, procurement receipt and shipment actions were not each separately driven live. Their endpoint/state contracts are mapped, shared mutation tests exercise frontend handling, and backend procurement/shipment regressions ran. Do not reinterpret the five live checks as exhaustive screen, role or domain-state coverage.

Browser automation was not run. Verification is **React/jsdom + real HTTP + FastAPI + PostgreSQL**, which the requested scope permits. Browser-enforced CORS/storage and visual/accessibility interaction remain separate acceptance checks. Server CORS preflight was verified independently.

### Rejected and unauthorized mutations

The live inventory test submits a quantity greater than usable stock and receives the real `409 Insufficient usable stock` error. An independent PostgreSQL snapshot, including balance and ledger count, is unchanged afterward.

The new disposable-PostgreSQL regression verifies an authorized facility writer, a read-only user (403), a wrong-facility request (404), invalid session (401), invalid quantity (422), changed-payload idempotency conflict (409) and insufficient stock (409). After rejected requests, the balance is 7 with exactly two successful stock transactions and two inventory audit records. Manual FastAPI requests remain protected even if frontend state is manipulated. Existing backend tests cover additional transfer, procurement, asset and operational scope/business rules.

Frontend regressions cover 400/401/403/404/409/422/429/503, network failure, validation, duplicate clicking, stable retry keys, refetch rendering, missing permissions, expired-session cleanup, narrow bed permissions, transition visibility, shipment prerequisites and actual report terminal states.

## Idempotency and state rules

- Inventory receive/issue/adjust, transfer creation and purchase-order receipt use the real body `idempotency_key`. An uncertain request retains its exact payload/key in user-scoped session storage. A regression remounts the form after a network failure and verifies the retry uses identical input/key.
- State transitions have row-lock/state checks. Repeating a completed transition is a conflict, not another stock movement. Transfer reservation, safety stock, usable batches, dispatch debits and receipt credits remain backend-owned.
- Purchase orders and shipments have unique references; suppliers/facilities have their existing uniqueness rules. Repeating a purchase-order reference is verified as 409; replaying a keyed procurement receipt does not double-receive stock.
- Aggregate writes use `expected_version`; a stale value is not silently overwritten. Ordinary metadata writes have their existing set-value semantics, not a newly invented version field.
- **Report-job creation has no backend idempotency contract.** A test confirms an extra key is rejected with 422 and two independent valid requests produce different jobs. The UI prevents rapid repeated submission and blocks automatic retry after an uncertain result, but cannot guarantee deduplication across tabs/clients or deliberately repeated actions.
- Maintenance and other event APIs without request keys retain their backend behavior. A network timeout must be reconciled with real records before another request. Button disabling is not described as backend idempotency.

## Permission and contract mismatches retained

1. **Facility/geography reads require `inventory.read`.** No new grant or backend permission change was made. Existing readable-directory administration requires that access. Narrow beds/workforce/aggregate screens use assigned/permitted facility UUID input instead of forbidden directory calls.
2. **Transfer scope includes both facilities.** Cancel/receive controls conservatively require an authorized successful shipment lookup (`procurement.read`) to establish eligibility. Without it the UI explains why those actions are unavailable; it does not grant procurement or inventory access.
3. **Order approval additionally requires `procurement.approve`; receipt requires `inventory.write`.** Supplier writes require global scope. Required relationships use real selectable records; missing directory permissions can limit available create forms.
4. **Shipment state is not independent of its parent.** Planned-only cancellation, valid parent movement states and shipment arrival before tracked receipt are respected. Arrival does not receive stock by itself.
5. **Safety-stock enforcement is at transfer approval in this backend.** Dispensing still uses its actual FEFO/expiry/recall/reservation rules; no unsupported additional rule was invented or removed.
6. **Report jobs have no running/cancel/retry or deduplication contract.** Staff/transfer reports have additional permissions/scope. Job filters are facility/kind/format only, unlike synchronous report filters, and generation is bounded to 500 rows.

Live testing found and fixed a duplicate React sibling-key defect between new action panels and existing data panels. It left stale supply controls when tabs changed. Action keys now have their own prefix; a regression asserts only one supply action section and exactly two transfer facility selectors. The test harness also now waits for confirmed writes **and completed refetch** before closing/reopening a form. Backend RBAC, scope, service code, migrations and state machines were not modified.

## Remaining legitimate read-only and unsupported actions

The matrix lists all 13 intentionally read-only families: medicine catalogue administration, barcode registry, stock policies, global recalls, threshold rules, escalation rules, recurring report schedules, user provisioning, role definitions, permission grants, user-role assignments, user scope assignments and password-change/reset confirmation flows. Existing read panels remain functional. A generic backend endpoint is not enough reason to expose a privileged action.

Seven deferred boundaries remain: cold-chain source ingestion, queued rule evaluation, notification delivery retry, optimizer ingestion/application, population import, offline synchronization and backup execution. Nine unavailable UI groups remain: public registration, individual bed/patient allocation, emergency simulation/activation, federated training, camera decoding, ambulance dispatch/crew assignment, unsupported settings persistence, prediction/risk/oxygen scenario controls and report-job cancel/retry.

No active operational placeholder was converted into local-only success. Removed fake transfer/dispensing confirmations remain removed. Local navigation, filters, draft fields, theme/language selection and dialog dismissal intentionally do not mutate the backend. Unreachable legacy demonstration files were preserved, not wired into the application.

## Final tests and checks

| Check | Result |
| --- | --- |
| Full backend suite after backend test additions | **85 passed, 1 skipped**, 93.95 seconds, 1 warning |
| Full frontend suite after final source/assertion changes | **126 passed, 13 skipped**, no failures |
| Dedicated live mutation suite | **5 passed**, no failures or skips |
| Production build | **PASS**: TypeScript and Vite; 2,396 modules |
| Alembic heads/current | Single current head **c83d9e124a35** |
| Alembic check against development PostgreSQL | **No new upgrade operations detected** |
| Development/disposable PostgreSQL | **sanjeevani_dev / sanjeevani_test**, PostgreSQL 16.9; PostGIS 3.5.2 |
| Redis | Development and disposable verification PING passed; version 7.4.11 |
| PostgreSQL/PostGIS/Redis tests | Applicable tests passed inside the full backend suite, including the added PostgreSQL authorization/idempotency regression |
| HTTP and configuration | Backend health and frontend 200; frontend API URL matches backend |
| CORS | Authenticated POST preflight allowed for localhost:5173 and 127.0.0.1:5173 with exact matching origins |
| OpenAPI/application | Live schema equals imported application schema; import and lifespan startup/shutdown passed |
| Python | Existing backend/.venv interpreter used; no package installation |
| Preservation/security/whitespace | PASS: git diff --check and trailing-whitespace checks; private files ignored; no known private secret values found in changed/untracked source |

The backend skip is `tests/test_postgres.py:124`: requires `ENABLE_TIMESCALEDB=1` and a compatible TimescaleDB/PostGIS server. It was not hidden or counted as passed. The warning is the existing Starlette TestClient/httpx deprecation warning.

The 13 frontend skips are opt-in live tests: 3 Phase 1 authentication, 5 Phase 3 data and 5 Phase 4 mutations. The five Phase 4 cases ran separately and passed. Phase 1/3 live suites were not rerun or counted as new successes. Their preserved results are documented in earlier reports.

Build warning: main JS is **1,030.91 kB**, gzip **297.98 kB**, exceeding Vite's 500 kB advisory threshold. This is a warning, not a failed build or completed performance audit.

Local evidence (ignored `tmp/`): `phase4-backend.xml`, `phase4-frontend.json`, `phase4-live.json`, `phase4-infrastructure.json`, `phase4-audit.json`, `phase4-control-inventory.json`, `phase4-preservation.json`. Earlier progress reports contain failures and are not substituted for the final results. The backend suite was not unnecessarily rerun after documentation-only changes.

## Development data and reproducibility

Docker Desktop and the existing services were initially stopped. Existing containers were restarted; none were recreated. No database, credentials, environment file or Docker volume was replaced. Development remains separate from the disposable PostgreSQL/Redis verification services.

`backend/scripts/verify_phase4_data.py prepare` created clearly labeled, isolated `DEV-P4-*` facilities, one medicine/batch, initial stock, a bed record and a test alert rule. Its ignored `tmp/phase4-fixture.json` records ownership. It checks local `sanjeevani_dev`, development mode, actual database identity and the existing administrator; it does not create/reset users. Preparation refuses to overwrite an existing manifest.

Only those owned development records were mutated. Stock transactions, completed transfers, resolved alert history and generated reports are deliberately retained as traceable evidence; immutable ledgers are not deleted to simulate cleanup. Bed occupancy was restored to its original seeded value. One initial test cleanup failed because it reopened the dialog too soon; the guarded fixture restore was executed, and the corrected live test subsequently verified UI-based restoration. Phase 3 fixtures were not used for Phase 4 writes.

The SQL `inspect` probe is read-only. The report-generation probe takes a table lock, requires exactly one pending report with the supplied ID and Phase 4 report facility, then calls the existing service. It refuses to process unrelated pending jobs. Alert reevaluation is limited to the owned Phase 4 rule. This controlled service execution is explicitly separate from worker/beat deployment.

Commands executed:

```powershell
# From backend, using existing isolated verification settings:
.venv/Scripts/python.exe -c "from dotenv import load_dotenv; load_dotenv('.env.local',override=True); import pytest; raise SystemExit(pytest.main(['-q','-rs','--tb=short','--junitxml=../tmp/phase4-backend.xml']))"
.venv/Scripts/python.exe -m alembic heads
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe -m alembic check
.venv/Scripts/python.exe scripts/verify_phase4_frontend.py
# From frontend:
npm test -- --reporter=json --outputFile=../tmp/phase4-frontend.json
npm run build
```

The live launcher reads the existing ignored account file and fixture manifest, passing credentials privately through the child environment. It never places passwords in CLI arguments or source. Repeating live tests makes additional explicitly labeled test transactions; it is not a destructive reset. Do not point these scripts at production or unowned data.

Actual development server commands were `.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000` from backend and `npm run dev -- --port 5173 --strictPort` from frontend. Existing configuration/startup/shutdown guidance remains in [DEVELOPMENT_ENV_VERIFICATION.md](../backend/DEVELOPMENT_ENV_VERIFICATION.md). No new teammate environment variable is required for ordinary UI use. Live checks require only the existing private test credentials/manifest; weather and Timescale configuration remain unchanged and outside Phase 4.

## Remaining blockers and next audit

- Resolve or explicitly accept the report-job backend deduplication gap before claiming duplicate-safe report submission across clients. Other non-idempotent event workflows need reconciliation guidance or backend support where business requirements demand exactly-once behavior.
- Verify unattended report worker/beat execution and external delivery before calling background processing operationally ready. Pending job creation is not evidence that a worker will consume it.
- Carry the facility/geography and shipment-read permission constraints into the final audit. Do not grant unrelated permissions to make forms visible.
- Browser E2E/visual acceptance, bundle performance, broader role/state live coverage, compatible Timescale testing and external providers remain separate readiness work.
- The 33 non-GET operations without frontend coverage are enumerated individually in the matrix. Some are intentionally governed/M2M/read-only boundaries, not missing buttons to be added automatically.

The next integration/readiness audit may begin with these items disclosed. No readiness work, commit, push, merge or deployment was performed in this phase.

Final preservation checks confirm the existing `frontend/package-lock.json` and every pre-existing backend file match the Phase 4 starting hashes. The selected 32 request schemas match actual OpenAPI. Import-graph verification reaches 77 source files and none of the six legacy mock/layout files listed in the matrix. `.venv`, backend/frontend private environments, private credentials, fixture manifests and production build output remain ignored. Secret scanning checked known private environment/credential values without printing them; this is not a guarantee against every possible secret pattern. Final check details are retained in ignored `tmp/phase4-final-checks.json` and `tmp/phase4-reachable.json`.

## Exact Phase 4 changed-file list

Relative to `tmp/phase4-preservation.json`, the preserved start-of-Phase-4 working tree. Earlier Phase 1-3 changes remain in Git status and are not misattributed to this list.

```text
backend/scripts/verify_phase4_data.py
backend/scripts/verify_phase4_frontend.py
backend/tests/test_phase4_mutations.py
frontend/API_INTEGRATION_MATRIX.md
frontend/PHASE4_MUTATION_MATRIX.md
frontend/PHASE4_OPERATIONAL_INTEGRATION.md
frontend/src/components/common/BackendData.tsx
frontend/src/components/common/MutationForm.tsx
frontend/src/modules/admin/AdminPage.tsx
frontend/src/modules/alerts/AlertsPage.tsx
frontend/src/modules/analytics/ReportsPanel.tsx
frontend/src/modules/beds/BedsPage.tsx
frontend/src/modules/disease/DiseasePage.tsx
frontend/src/modules/equipment/EquipmentPage.tsx
frontend/src/modules/equipment/OperationsActions.tsx
frontend/src/modules/facilities/FacilitiesPage.tsx
frontend/src/modules/facilities/FacilityActions.tsx
frontend/src/modules/facilities/SupplyActions.tsx
frontend/src/modules/facilities/WarehouseDashboardPage.tsx
frontend/src/modules/inventory/InventoryActions.tsx
frontend/src/modules/inventory/InventoryPage.tsx
frontend/src/modules/patients/PatientsPage.tsx
frontend/src/modules/workforce/WorkforcePage.tsx
frontend/src/services/dataApi.ts
frontend/src/services/httpClient.ts
frontend/src/services/mutationSchemas.ts
frontend/src/test/dataIntegration.test.tsx
frontend/src/test/mutations.test.tsx
frontend/src/test/mutationsLive.integration.test.tsx
```
