# Functional Completion & Data Enrichment audit

Subsequent account-only addition: see [DEVELOPMENT_ACCOUNT_MATRIX.md](DEVELOPMENT_ACCOUNT_MATRIX.md)
for the latest role audit, test results and password-source mechanism. The working-tree
inventory below is the prior phase checkpoint, not the final account-addition inventory.

Date: 2026-10-03. Branch: `feature/functional-completion`.

Implementation and local API/React verification are complete for the bounded scope
below. Browser visual acceptance remains **UNAVAILABLE**, not passed. Unsupported
features are explicitly deferred rather than filled with demonstration numbers.
No commit, push, merge, deployment, schema migration, dependency installation,
credential change, CSV rewrite or full catalogue import was performed.

## Audit method and coverage

Inspected `frontend/src/app/router.tsx`: **80 leaf routes, 27 page components**,
plus root/portal index redirects and the catch-all redirect. The static import
closure from `App.tsx` contains 76 TypeScript/TSX files. The actual dependency chain
is page -> `useBackendData` / `dataApi` -> authenticated `httpClient` -> FastAPI
route -> permission/scope checks -> service/repository -> PostgreSQL. The API's
current OpenAPI has **125 operations**. This phase adds an optional response field,
not new API operations; it does not claim all operations have UI coverage.

The audit combined source tracing, actual OpenAPI, SQL reads, real HTTP, targeted
regressions, and rendered React with real HTTP. It does not infer a feature works
from its component name or from an HTTP 200 alone. Route aliases share the component
and endpoint evidence below; not every URL received a separate browser visit.

Classification used throughout:

- **A**: Real database/API data available, including explicitly synthetic development records.
- **B**: Model/API exists; meaningful sample data or configured records are absent.
- **C**: Source enrichment is required; do not manufacture missing source facts.
- **D**: Working backend capability or required external implementation is missing.
- **E**: Intentionally deferred or read-only workflow (including UI-only status pages).

Multiple letters distinguish working and unavailable areas of the same page.
`data present` below refers to the bounded development dataset, not every facility.
Unselected facility queries show a selection prompt. Empty API arrays show a
scope/filter-specific empty state; denied and failed requests show errors, not zeros.

Role notation: **Admin** = SUPER_ADMIN; **N+** = National and Admin; **S+** = State,
National and Admin; **D+** = District, State, National and Admin; **F+** = all five
portal aliases. **Common** = any authenticated user with the required backend
permission. Role names select a portal; they do not supply grants. Every route is
also checked by `canAccessPath`; actual backend scope remains authoritative.

## Page and feature matrix

All endpoints are prefixed `/api/v1`. GET is implied except where stated.
The complete path inventory follows this matrix.

| Page/component | Roles and capability | Backend endpoints | Data source / present? | Functional and empty/error behavior | Class | Missing capability / bug / deferred work |
| --- | --- | --- | --- | --- | --- | --- |
| LoginPage | Public; resulting server grants | POST `/auth/login`, `/users/me`; POST refresh/logout | Users, roles, permission and scope bindings; four dev accounts | Real form/JWT/me/redirect checked for all four; credential/network errors fail closed | A | No demo bypass; browser acceptance unavailable |
| RegisterPage | Public | None; governed POST `/users` exists outside this page | No self-registration data | Explicit unavailable notice and login link | E | Public account creation intentionally prohibited |
| MFAPage | Public help; MFA enforced by login backend | Login accepts MFA proof | Provider not configured for dev accounts | Instructions only; no fake verification | D/E | Enrollment/provider UI and external proof verification configuration |
| ForgotPasswordPage | Public request | POST `/auth/password/reset/request` | PasswordReset/delivery hook | Conditional acknowledgement; real errors surfaced | D/E | Delivery provider and reset-confirm UI; no email delivery claimed |
| UnauthorizedPage | Public error destination | None | Router state | Access-denied page | E | UI-only; not an operational metric |
| SuperAdminDashboardPage | Admin + global + admin.users | `/users`, tab endpoints below | User catalogue present | Renders AdminPage, not operational KPI dashboard | A/E | Administration summary is not a new analytics endpoint |
| AdminPage: users/roles | Admin + global + admin.users | `/users`, `/roles`, `/permissions` | 6 users, 4 roles, 26 permissions | Paginated reads; real failure/empty states | A/E | Provisioning, grant edits and scope assignment remain governed API/CLI workflows |
| AdminPage: audit | Admin + global + audit.read | `/audit-logs` | Immutable audit events present | Real paginated audit rows | A | No fabricated audit history |
| AdminPage: monitoring | Admin + global + admin.config | `/health`, `/admin/config`, `/admin/backups/status` | API liveness/config present; backup latest null, healthy false | Displays reported state, not invented readiness | A/D | CPU/pool/cache/node telemetry and backup execution/restore verification absent |
| SettingsPage | Admin config permission | `/admin/config`; local theme store | Public configuration available | Browser-local theme; disabled unimplemented settings; availability notice | A/E | Contrast/audio/offline frequency not connected; WCAG claim not independently certified |
| ProfilePage | Any signed-in user | Identity from `/users/me` | Actual username, roles, capabilities and scope | Real identity display | A/E | Profile editing/password-change UI deferred |
| NationalDashboardPage | N+ + reports.read | `/facilities`, `/alerts`, `/purchase-orders`, `/inventory`, `/assets/{kind}`, `/operations/{kind}`, `/reports/{kind}` | Source directories plus synthetic operational records | Counts/bed chart fetched from DB; selector, errors and empty states | A/D | No national medicine score, resilience, forecasts or oxygen runway |
| StateDashboardPage | S+ + reports.read | Same BackendDashboard calls | Actual authorized scope, not inferred state totals | Same working dashboard; no live state-account fixture | A/C | State jurisdiction requires real assignments; source lacks block/district links |
| DistrictDashboardPage | D+ + reports.read | Same BackendDashboard calls | Actual authorized scope | Same working dashboard; no live district-account fixture | A/C | No fabricated district assignments or district benchmark |
| FacilityDashboardPage | F+ + reports.read | Same BackendDashboard calls | Three seeded source facilities; depot for stock | Rendered live for dev roles, selected stock count and 18/20 beds checked | A/D | Inventory role correctly lacks staff/assets reads; per-card denied state |
| RegionalDashboard | N+/S+ + reports.read | Same BackendDashboard calls | Scoped resource data | Working shared dashboard, not ranked state/district comparison | A/D/E | Comparison/benchmark capability deferred; route labels overstate specialized analysis |
| FacilitiesPage | Admin/N+/S+/D+/Common + inventory.read | `/facilities`, `/facilities/{id}`, `/geography/{kind}`; authorized POST/PATCH controls | 58 facilities; 50 source imports | Real directory/details/search/type/status/hierarchy filters; empty/error states | A/C | 50 imports lack verified hierarchy/exact coordinates; directory state filters still use real hierarchy |
| InteractiveResourceMap | N+/S+/D+/Common + inventory.read | `/facilities`, `/geography/{kind}` | 1 recorded point + 23 annotated city references | 24 plottable facilities, grouped shared points, labeled approximation, filters/popups/errors | A/C/D | 34 unlocated; no risk/heatmap/crisis polygons; browser rendering unavailable |
| InventoryPage: ledger/batches/history | N+/S+/D+/F+/Common + inventory.read; writes require inventory.write | `/medicines`, `/inventory`, `/inventory/transactions`, `/batches/{id}/trace`; POST receive/issue/adjust | 200 imported medicines; seeded stock/ledger | Real FEFO-sorted records and mutations; no facility -> prompt | A | Shared expiry-route stale tab fixed; unknown medicine units remain unspecified |
| InventoryPage: expiry/stock policy | Same inventory reads | `/inventory/expiry`, `/inventory/days-of-stock` | Warning windows/safety stock and near-expiry lots present | Real null/insufficient-history status, not a zero forecast | A/B | Only one day of sample consumption; no justified days-of-stock/reorder projection yet |
| InventoryPage: barcode/recalls | Same inventory reads | `/barcodes/lookup`, `/recalls` | No registered barcode/recall sample | Real 404/empty register, explicitly read-only administration | B/E | Camera scanning unimplemented; no fake product barcode or recall manufactured |
| ColdChainPanel | inventory.read | `/operations/temperatures`, `/cold-chain/series` | Two synthetic observations, one excursion; shipment-linked | Observations and time-window series return database records | A | Samples do not imply installed sensors or calibrated clinical storage |
| WarehouseDashboardPage | N+/Common + inventory.read or procurement.read; each tab rechecks capability | `/warehouses`, stock, `/suppliers`, metrics, `/purchase-orders`, details, `/shipments`, history, `/transfers`, details; supported mutations | 1 warehouse, 2 suppliers, 3 POs, 1 shipment, 4 transfers including prior fixtures | Scoped tables/actions; restricted users denied global-only operations | A/D | Navigation omission fixed; utilization, drivers and optimized ETA unsupported |
| BedsPage | N+/S+/D+/F+/Common + beds.read; beds.write for mutations | `/operations/beds`, `/beds/{id}/history`; PUT `/beds` | Three labeled seeded bed groups/history | Availability and occupancy derived from stored values; no zero-capacity division | A/D | Patient allocation/reservation workflow absent |
| WorkforcePage | N+/S+/D+/F+/Common + workforce.read/write | `/operations/{staff,shifts,attendance}`, `/staff-roles`; staff/shift/attendance mutations | Three seeded staff/shift/attendance rows | Tables/actions work; attendance alias now switches tab on navigation | A/D | No validated doctor classification, workload model, biometric or paging integration |
| PatientsPage | N+/S+/D+/F+/Common + integration.read; integration.write for aggregate mutation | `/operations/footfall`; PUT `/aggregates/footfall` | Three labeled synthetic daily aggregates | Real aggregates, selector and empty state | A/D | Individual patients, triage queue, waiting times, hourly admission/discharge absent |
| DiseasePage | N+/S+/D+/Common + integration.read/write | `/operations/disease-counts`; PUT `/aggregates/disease-counts` | Imported sample facilities have no disease observations; prior isolated fixture elsewhere | Honest empty state; aggregate contract exists | B/D/E | No clinical observations invented; no outbreak polygons, predicted severity or growth model |
| EquipmentPage | F+/Common + equipment.read/write | `/assets/{equipment,ambulances}`, maintenance GET/POST; asset POST/PUT | Three seeded equipment, maintenance and ambulance records | Real status/history; ambulance alias now switches tab | A/D | No dispatch/ETA/crew/oxygen telemetry or uptime history model |
| AlertsPage | N+/S+/D+/F+/Common + alerts.read; alerts.manage for actions | `/alerts`, `/alert-rules`, `/notifications`, `/escalation-rules`, history; POST alert actions | 11 alerts including 7 from base seed; no configured escalation/notification sample | Real incident/rule tables; acknowledgement/resolution permission-gated | A/B/E | Notification delivery/recipient escalation not manufactured to fill tables |
| AIDashboard: reports | N+/S+/D+/Common + reports.read/export | `/reports/{stock,expiry,transfers,procurement,staff,beds,emergency}`, POST `/report-jobs`, status/download | Database reports populated; existing report-job capability | Reports/downloads; staff requires workforce.read; job pending is not success | A/E | Job execution still requires Celery; no new job completion claim in this phase |
| AIDashboard: trends/context | Same routes; integration.read per panel | `/datasets/medicine-consumption`, `/optimization/context`, weather/population | Issue history exists; stock context exists; population absent | PostgreSQL date/VARCHAR 500 fixed and live consumption now matches ledger | A/C/D | Weather requires exact recorded location then configured provider; no inferred weather at city point |
| AIDashboard: recommendations/forecasts | Same routes; integration.read for recommendation list | `/optimization/recommendations`; no forecast endpoint | Recommendation list empty | Explicit unavailable prediction/SHAP/cost/resilience/benchmark cards | B/D/E | External optimization producer and forecast/explanation APIs absent; no fabricated AI values |
| EmergencyPage | N+/S+/D+/Common + emergency.activate; report permissions additionally required | `/reports/emergency` via ReportsPanel | Scoped emergency report data available | Reports usable; scenario/activation controls explicitly unavailable | A/D/E | Crisis activation, routing, mobilization, vulnerability and simulation contracts absent |
| FederatedAIPage | N+/Common + federation.manage | No working training/node telemetry endpoint in this FastAPI contract | None | Explicitly unavailable, no fabricated graphs | D/E | Rounds, accuracy, convergence, privacy budget, node health and orchestration belong to later AI integration |

### API-to-database ownership

| Endpoint family | Backend implementation | Models/tables and authorization |
| --- | --- | --- |
| auth/users/roles | `endpoints/identity.py`, `services/identity.py`, `services/admin.py`, `security/auth.py` | users, roles, permissions, role_permissions, user_roles, user_facilities/user_districts, auth_sessions; server identity, global admin restrictions |
| geography/facilities | `endpoints/geography.py`, `services/geography.py`, `services/location_context.py` | facilities/countries/states/districts/blocks; inventory.read and facility_filter; optional location context from owned audit provenance only after scope filtering |
| medicines/inventory/stock | `endpoints/platform.py`, stock/transfer routes; `services/inventory.py`, `stock.py`, `transfers.py` | medicines, medicine_batches, medicine_inventory, stock_transactions, stock_policies, transfer_*; dedicated permissions, facility scope, ledger/FEFO/safety/idempotency |
| supply | `endpoints/supply.py`, `services/supply.py` | suppliers, warehouses/warehouse_inventory, purchase_orders/items/history, shipments/history; procurement and inventory permissions, state machines and source/destination scope |
| operations/assets | operations/assets endpoints and services | bed_capacity/history, staff/roles, shifts, attendance, patient_footfall_aggregates, disease_counts, equipment/maintenance_records, ambulance_records, temperature_observations/cold_chain_samples; dedicated capability + facility scope |
| alerts | alerts endpoints/services | alert_rules, alerts, notification_logs, escalation_rules/history; scoped incident reads and management; notification recipients |
| reports/jobs | reports/report_jobs endpoints and services, exports/tasks | Queries existing operational tables; report_jobs/schedules; reports.read/export, extra workforce permission, scoped job ownership |
| datasets/integrations | integrations endpoints; datasets/integrations services | UTC issue aggregation, population_snapshots, weather_cache, optimization_recommendations, barcodes, backup_records; integration permissions and existing per-endpoint scope/global constraints |

No permissions were broadened. The existing facility/geography `inventory.read`
coupling remains: bed/workforce-only accounts use the explicit facility-ID fallback
instead of receiving inventory rights. Geography and medicine catalogues are
shared reference data, not automatically jurisdiction-filtered directories.
Population reads currently accept district IDs without a district-scope predicate;
the table is empty here. Review whether that reference-data policy is appropriate
before importing any restricted demographic dataset.

## Role and account verification

| Account / alias | Database role and scope | Result |
| --- | --- | --- |
| dev-data-admin / SUPER_ADMIN | administrator, global, 26 capabilities | PASSED real form -> JWT -> me -> admin landing; operational shared links and data |
| dev-data-operator / FACILITY_ADMIN | dev_data_operator, one facility, 14 capabilities | PASSED real form, portal, scopes, operational reads and navigation |
| dev-data-inventory / FACILITY_ADMIN | dev_data_inventory, three facilities plus depot, 8 capabilities | PASSED; workforce navigation absent and staff API 403; no admin UI/grant |
| dev-data-reader / FACILITY_ADMIN | dev_data_reader, one facility, 9 capabilities | PASSED; read-only controls, rejected bed PUT 403, outside inventory 404 |
| National aliases | national_admin/national_officer -> NATIONAL_ADMIN | Static route/capability audit and existing routing regression tests; NOT RUN as a live account (no such DB role/account) |
| State aliases | state_admin/state_officer -> STATE_ADMIN | Same; no invented state assignments or global grants |
| District aliases | district_admin/district_officer -> DISTRICT_ADMIN | Same; no trusted source district/block assignments to seed |

All four live accounts' `/users/me` IDs, backend roles, exact permission sets and
facility scopes were compared with PostgreSQL. Restricted facility lists matched
assigned IDs. Each tested logout invalidated the prior access token (401). The
`arpan` fingerprint matches the pre-data-foundation baseline: ID, password hash,
active flag, token version, scope and role IDs. No login/reset was attempted for it.
No new users, role grants or passwords were added in this phase.

The role sidebar now displays backend role names, not a misleading alias-based
security tier. Shared map/directory/supply/report links were added to the facility
portal and operational links to the admin portal; existing capability filtering
still controls visibility. RoleGuard remains the route gate, and FastAPI remains
the authorization boundary. Unknown roles/permissions cannot grant frontend access.

## Empty/misleading behavior and disposition

| Finding | Class | Disposition |
| --- | --- | --- |
| Imported facilities mostly invisible on map | C | 23 reviewed city annotations exposed through real API; other records remain unlocated |
| Shared map point overlaps hide other city facilities | A | Group same-location points and list all records in popup; no random jitter |
| Facility/inventory users lack discoverable supply/map/report links | A | Fixed navigation using existing common routes/capability checks |
| Inventory/expiry, workforce/attendance, equipment/ambulance stale tab on route change | A | Fixed effects keyed to pathname, regression tested without remount |
| Medicine consumption produces PostgreSQL 500 | A | Reproduced date >= VARCHAR failure; bind date objects; PostgreSQL and live React tests cover fix |
| Synthetic operational counts look like actual hospital observations | A | Development notice on operational headings, including development accounts in a production build; seeded labels retained |
| Empty ambulance/maintenance/shipment/cold-chain views | B | Bounded service-based enrichment, transaction receipt and replay checks |
| Zero batch/staff/equipment cards before selecting facility | A | Already selection-gated; no fake zero rendered while disabled/loading/error |
| Days of stock/reorder suggestions null | B | Correct insufficient_history result: one issue-history day; kept null rather than fabricating historical consumption |
| Unassigned state/district filters exclude source facilities | C | Explicit limitation; map state display filter can use annotated city-state text, directory and backend scopes require real hierarchy |
| Disease aggregates at source facilities absent | B/E | Keep empty; no invented clinical observations |
| Barcode/recall/notification/escalation lists empty | B/E | Valid empty contracts; administration/delivery require deliberate workflow, not artificial records |
| Population absent / weather unavailable | C/D | No population source or exact source-facility coordinates; no enrichment masquerading as exact weather location |
| AI/federated/risk/oxygen/cost/ETA/triage charts unsupported | D/E | Existing explicit unavailable panels remain; no synthetic AI/clinical statistics |
| Regional comparison and forecasting URLs reuse generic pages | D/E | Documented: regional dashboard is scoped resources; forecasting route lands on analytics with unavailable forecast tab, not a working prediction |
| User/grant administration, recall control, offline upload, camera scanning | E | Existing read-only/disabled states preserved; no false success confirmations |
| Settings theme/high contrast/audio/sync | E | Theme state toggle exists; comprehensive theme/accessibility visual behavior unverified. Other controls remain explicitly disabled |
| Legacy HomePage/TopBar/mockData demonstrations | E | Unreachable from current App/router import graph; unchanged, must not be reintroduced into production routes |

No active operational route imports `services/mockData.ts` or `pages/HomePage.tsx`.
The retained legacy HomePage contains fixed KPIs and demonstration toast text;
it is not mounted or a runtime data source. No random frontend operational numbers
were found in the active dependency graph. UUID generation for mutation idempotency
is not an operational metric. Disabled unsupported controls are intentional,
not silent successful actions. There is no evidence of a permanently unresolved
query in the exercised screens: disabled queries prompt for input, and transport
timeouts/errors are surfaced. Unvisited browser-only behavior is not certified.

## Seed and geospatial coverage

The original 200 medicine / 50 facility catalogue limit is unchanged. This phase
adds no medicines, facilities, countries, states, districts, blocks or users.
Base stock, beds, workforce, footfall, suppliers, transfers, policies and alerts
were reused. Explicit CLI: `python -m scripts.development_data enrich --seed 20261003`.
It requires the existing owned operations receipt, local development DB guard and
the same advisory lock as the other development commands. All enrichment writes
are one transaction, with a versioned mutation receipt and reference snapshot hash.
Same seed/hash replays without writes; a changed reference snapshot is rejected.

| Added entity | Count |
| --- | ---: |
| Approximate city provenance annotations (included in audit row total) | 23 |
| Ambulances / maintenance records | 3 / 3 |
| Purchase order / line / procurement history | 1 / 1 / 5 |
| Shipment / shipment history | 1 / 4 |
| Medicine batch / inventory row / stock transaction | 1 / 1 / 1 |
| Temperature observations / cold-chain samples | 2 / 2 |
| Mutation receipts / audit events | 2 / 42 |

These counts exclude auth verification sessions/audits. Existing equipment's last/
next maintenance dates were updated through its maintenance service; its name,
identity and source facility were not replaced. The shipment was created only
after ordering, moved through legal states, arrived, then its PO was received.
Synthetic observations carry an explicit SYNTHETIC source. No sensor, clinical
diagnosis, AI activity or actual hospital observation is implied. Rerunning enrichment
left all application table counts unchanged, and stock remains ledger-balanced.

Repository coordinates found in old mock data/test fixtures were not reused.
The small committed reference snapshot contains ten GeoNames populated-place points,
selected by exact city name and country IN, with states from its admin1 reference.
It records retrieval date, both download hashes, GeoNames IDs and source links.
These WGS84 points are approximate city references, **not exact hospitals or
mathematically calculated centroids**. Data is attributed under CC BY 4.0 and has
no accuracy warranty. [GeoNames format and license](https://download.geonames.org/export/dump/readme.txt).

Enrichment performs no network geocoding: it matches exact normalized city/state
labels for at most 50 imported ownership records. Unmatched/ambiguous, already
located, inactive or address-changed records are not assigned a point. The current
bounded match yields 23 annotations. Annotations retain source-row provenance in
immutable `audit_logs` and are exposed as typed `location_context` on authorized
facility directory/detail responses. They are not stored in Facility latitude/
longitude or block/district columns. If the facility address/code changes or exact
coordinates are later recorded, the annotation is not exposed.

The separate field avoids treating city points as exact for existing PostGIS nearby,
weather, FHIR or routing consumers. No new migration was necessary for this bounded
development-only annotation; a durable general geocoding workflow would warrant a
dedicated reviewed data model rather than growing the audit-provenance lookup.

| Coordinate coverage | Count |
| --- | ---: |
| Total development facilities | 58 |
| Existing recorded coordinates (not independently verified) | 1 |
| Approximate city references | 23 |
| Plottable facilities, including grouped shared points | **24** |
| Remaining without any map location | **34** |
| Imported facilities with exact coordinate fields | **0 / 50** |
| Imported facilities without even approximate reference | **27 / 50** |

OSM tiles/attribution are unchanged. Dashed city markers, popup precision/source
labels, and source-directory notices distinguish approximations. State map filters
include reviewed city-state labels; district filters do not infer jurisdictions.
That display-only distinction never changes authorized facility sets. Further
precise enrichment requires reliable address/coordinate evidence and review.

## Dashboard calculations and real HTTP evidence

Counts use complete paginated directories in the authorized scope: active facilities,
unresolved alerts, purchase orders; selected-facility stock batch records, equipment,
ambulances and staff. Bed occupancy is sum(occupied)/sum(capacity), with explicit
empty/zero-capacity handling. Footfall comes from recorded daily aggregates.
These numbers are database-derived; in this environment they include labeled
synthetic fixtures, not real hospital measurements.

Live selected facility: A Beautiful Mind Clinic. Its post-enrichment inventory
contains **10 batch rows**; beds **18 occupied / 20 capacity (90%)**, one seeded
staff member, one seeded equipment item and one seeded ambulance. Source catalogue
totals remain **202 medicines / 58 facilities**, including prior fixtures. Global
reads return **2 suppliers, 1 warehouse, 3 POs, 1 shipment, 4 transfers, 11 alerts**.
Stock, beds, staff, procurement and expiry report rows are present (10/1/1/2/1 for
the selected facility). Cold-chain observations and series each return two rows.
Consumption for the seeded UTC day matches the ledger's issue quantity, not a
forecast. `days_of_stock`, reorder point and suggested quantity remain null with
`insufficient_history`, history_days=1; current stock=4 and safety stock=2.

`scripts/verify_functional_completion.py` compares paginated HTTP IDs with SQL IDs,
identity/grants/scope with SQL bindings, stock quantities with ledger sums, and UTC
consumption with an independent timestamp-bounded SQL sum. The rendered React test
uses that independently collected evidence to verify visible stock, beds, staff,
procurement, map and consumption output after real form login. No fetch/JWT/API
transport mocks are used in these opt-in tests. Shared test setup substitutes
Leaflet DOM rendering only; **this is not browser tile/visual verification**.

Additional live audit: health/config/roles/permissions return real values; backup
status is healthy=false with no latest artifact; notifications, escalation rules,
recalls, population and recommendations are empty. Weather for imported facilities
returns **409 location unavailable**; approximate points intentionally do not satisfy
that contract. A configured provider is still required for actual located facilities.

## Verification and remaining gates

| Check | Final result |
|---|---|
| New enrichment + existing development-data + PostgreSQL consumption + integration regressions | **PASSED: 13 tests** |
| New frontend regressions | **PASSED: 5 tests**, also included in normal suite |
| Complete backend `python -m pytest -q -rs`, private disposable infrastructure configuration loaded | **PASSED: 102; SKIPPED: 1** TimescaleDB test; existing Starlette/httpx deprecation warning |
| PostgreSQL/PostGIS and Redis integration tests | **PASSED**, enabled in the complete suite against disposable verification infrastructure; development connectivity and actual HTTP data verified separately |
| Normal frontend `npm test`, Node 24.15.0 | **PASSED: 137; SKIPPED: 17** opt-in live tests; 6 test files passed, 4 skipped |
| `FUNCTIONAL_LIVE_TEST=1 npm test -- src/test/functionalLive.integration.test.tsx` | **PASSED: 4** real-account rendered React/HTTP tests, including PostgreSQL consumption rendering; no mocked HTTP |
| TypeScript and production `npm run build` (`tsc && vite build`) | **PASSED**; existing >500 kB chunk warning (main JS 1,034.26 kB, gzip 298.95 kB) |
| Development Alembic heads/check | **PASSED**: one head `c83d9e124a35`, no new upgrade operations |
| Independent SQL-backed HTTP verification | **PASSED**; records/quantities/scopes matched SQL, not just HTTP 200; original `arpan` fingerprint unchanged |
| Actual browser/map visual acceptance | **UNAVAILABLE**, not passed |
| Historic opt-in Phase 1–4 frontend fixture suites | **NOT RUN** in this phase; their 13 skips remain visible, alongside the 4 separately executed new live tests |
| TimescaleDB-specific verification | **SKIPPED**: compatible TimescaleDB/PostGIS test server and `ENABLE_TIMESCALEDB=1` unavailable |

Backend commands use `backend/.venv/Scripts/python.exe`. For the full suite, the
existing ignored `.env.local` was loaded with `dotenv.load_dotenv(..., override=True)`
before `pytest.main(['-q','-rs'])`, targeting the disposable database, not development.
Live verification uses `python -m scripts.verify_functional_completion --api
http://127.0.0.1:8001`; private credentials and SQL facts remain under ignored `tmp/`.
The live test initially exposed a test-picker timing race (another picker loaded
first); it now waits for the dashboard picker's own option. Final rerun: all four
passed without weakening data assertions. The PostgreSQL consumption regression
was first run failing, then passed after binding date values as SQL dates.
Browser control could not initialize: native computer-use pipe unavailable, and
browser tool reported no available browser. No screenshot/login/browser result is
claimed. Live National/State/District accounts are also NOT RUN because no such
accounts exist in this development dataset; no permissions were invented to create them.

For local HTTP verification a separate backend runs on **127.0.0.1:8001** because
an existing API occupies 8000. Vite runs on **127.0.0.1:5173**, with process-local
`VITE_BACKEND_URL=http://localhost:8001`. CORS preflight for localhost:5173 returned
the matching origin, and Vite's served client contains port 8001. No environment
file was overwritten. Normal documented ports remain configurable.

Remaining backend/product gaps: AI training/forecasting and telemetry APIs, external
optimization producer, exact geographic enrichment, population source integration,
weather configuration, notification delivery/escalation configuration, backup
execution/restore verification, emergency dispatch/simulation, individual patient
workflows, and adequate historical observations for projections. Existing APIs
for role management, recalls, barcode registration, sync, FHIR, population ingestion,
recommendation actions and backup reporting are not automatically new UI requirements;
their unsupported/read-only frontend workflows remain deferred.

Remaining UI/UX work: many mutation fields still require UUIDs; global/multi-facility
users must choose a facility; regional-comparison/forecast labels imply more than
their shared pages provide; generic API tables are functional but not polished;
full theme/accessibility/responsive visual acceptance and browser map interaction
remain unverified. No design-system/sidebar rewrite or decorative metrics were added.

Safe to review/commit as a bounded development improvement after inspecting the
listed diff. This is not a claim of full product completeness, deployment readiness,
successful browser acceptance, or approval to merge. No commits or pushes were made.

## Complete route inventory

The following inventory groups all 80 leaf routes by the 27 components. Each maps
to the feature/capability/endpoint/data classification above. Root `/`, five portal
index routes and `*` are redirects, not additional data screens.

| Page component | Routes |
|---|---|
| AdminPage | `/admin/users`, `/admin/roles`, `/admin/monitoring`, `/admin/audit-logs` |
| AIDashboard | `/national/forecasting`, `/national/analytics`, `/state/analytics`, `/district/analytics`, `/analytics` |
| AlertsPage | `/national/alerts`, `/state/alerts`, `/district/alerts`, `/facility/alerts`, `/alerts` |
| BedsPage | `/national/beds`, `/state/beds`, `/district/beds`, `/facility/beds`, `/beds` |
| DiseasePage | `/national/disease`, `/state/disease`, `/district/disease`, `/disease` |
| DistrictDashboardPage | `/district/dashboard` |
| EmergencyPage | `/national/emergency`, `/state/emergency`, `/district/emergency`, `/emergency` |
| EquipmentPage | `/facility/equipment`, `/facility/ambulance`, `/equipment` |
| FacilitiesPage | `/admin/facilities`, `/national/facilities`, `/state/facilities`, `/district/facilities`, `/facilities` |
| FacilityDashboardPage | `/facility/dashboard` |
| FederatedAIPage | `/national/federated-ai`, `/federated-ai` |
| ForgotPasswordPage | `/forgot-password` |
| InteractiveResourceMap | `/national/map`, `/state/map`, `/district/map`, `/map` |
| InventoryPage | `/national/inventory`, `/state/inventory`, `/district/inventory`, `/facility/inventory`, `/facility/stock`, `/facility/expiry`, `/inventory`, `/expiry` |
| LoginPage | `/login` |
| MFAPage | `/mfa` |
| NationalDashboardPage | `/national/dashboard` |
| PatientsPage | `/national/patients`, `/state/patients`, `/district/patients`, `/facility/patients`, `/patients` |
| ProfilePage | `/facility/profile`, `/profile` |
| RegionalDashboard | `/national/states`, `/national/district-comparison`, `/state/districts` |
| RegisterPage | `/register` |
| SettingsPage | `/admin/config`, `/admin/settings`, `/settings` |
| StateDashboardPage | `/state/dashboard` |
| SuperAdminDashboardPage | `/admin/dashboard` |
| UnauthorizedPage | `/unauthorized` |
| WarehouseDashboardPage | `/national/warehouses`, `/warehouses` |
| WorkforcePage | `/national/workforce`, `/state/workforce`, `/district/workforce`, `/facility/workforce`, `/facility/attendance`, `/workforce` |

## Final working-tree boundary

`git diff --check`: **PASSED**. All 24 changed/new text files were checked for
trailing whitespace and literal private credential/secret values: no matches.
This is a bounded check, not a comprehensive security certification.
No migrations, lockfiles, root CSV datasets, credentials or environment files changed.
The new small attributed city-reference JSON is intentional enrichment metadata.
Private files and `.venv` remain ignored. No unrelated changes were found.

Tracked-only `git diff --stat`: 16 files, 138 insertions, 12 deletions.
Eight new files are listed separately below; Git diff stat does not include them.

Exact `git status --short --untracked-files=all` (nothing staged):

```text
 M DEVELOPMENT.md
 M backend/app/api/v1/endpoints/geography.py
 M backend/app/schemas/outputs.py
 M backend/app/services/datasets.py
 M backend/app/services/geography.py
 M backend/scripts/development_data.py
 M backend/tests/test_postgres.py
 M frontend/src/app/navigationConfig.ts
 M frontend/src/components/common/BackendData.tsx
 M frontend/src/components/common/RoleSidebar.tsx
 M frontend/src/modules/equipment/EquipmentPage.tsx
 M frontend/src/modules/facilities/FacilitiesPage.tsx
 M frontend/src/modules/inventory/InventoryPage.tsx
 M frontend/src/modules/map/InteractiveResourceMap.tsx
 M frontend/src/modules/workforce/WorkforcePage.tsx
 M frontend/src/services/backendTypes.ts
?? FUNCTIONAL_COMPLETION_AUDIT.md
?? backend/app/services/location_context.py
?? backend/scripts/data/development_city_references.json
?? backend/scripts/development_enrichment.py
?? backend/scripts/verify_functional_completion.py
?? backend/tests/test_development_enrichment.py
?? frontend/src/test/functionalCompletion.test.tsx
?? frontend/src/test/functionalLive.integration.test.tsx
```
