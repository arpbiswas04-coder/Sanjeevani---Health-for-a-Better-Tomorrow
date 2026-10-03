> Current status: see [Phase 5 readiness audit](../FINAL_READINESS_AUDIT.md) and [supported setup](../DEVELOPMENT.md). This report retains historical phase results. Phase 5 adds optional report-job idempotency (`ReportJobRequest`), real Celery worker/Beat verification, and explicit production API configuration. Earlier statements about those gaps are superseded.

# Phase 3 frontend -> backend integration matrix

> The original tables below preserve the Phase 3 read-integration snapshot. Current mutation coverage and dispositions are recorded in the Phase 4 addendum at the end and in [PHASE4_MUTATION_MATRIX.md](PHASE4_MUTATION_MATRIX.md).

Audited 2026-10-02 on `integration/frontend-backend`. Contract: current FastAPI-generated OpenAPI and endpoint/service code, not old endpoint documentation. All paths below use `/api/v1` unless explicitly stated.

Logical areas are counted once, even when exposed through several role-route aliases. CONNECTED means the named read/data flow exists, not that all backend mutations or external providers are available. PARTIAL rows state the missing capabilities explicitly.

## Frontend area audit

| Area / implementing frontend files (under `src/`) | Required data | Discovered source -> current source classification | Endpoint(s) and method | Integration status | Limits / unsupported data |
| --- | --- | --- | --- | --- | --- |
| Authentication<br>modules/auth/LoginPage.tsx; services/authService.ts; store/authStore.ts | Identity, JWT and session lifecycle | REAL_BACKEND (Phase 1 preserved) | `POST /auth/login`<br>`GET /users/me`<br>`POST /auth/refresh`<br>`POST /auth/logout` | CONNECTED | Form credentials; real grants, refresh and logout; no demo fallback. |
| Profile and permission-aware shell<br>modules/auth/ProfilePage.tsx; components/common/RoleTopBar.tsx; RoleSidebar.tsx; CommandPalette.tsx; app/authorization.ts | User identity, scope and navigation | REAL_BACKEND + FRONTEND_ONLY | `GET /users/me` | CONNECTED | Role labels are presentation only. Runtime grants drive visibility; backend enforces access. |
| Recovery and MFA<br>modules/auth/ForgotPasswordPage.tsx; MFAPage.tsx | Recovery request and MFA proof | REAL_BACKEND + BACKEND_NOT_AVAILABLE | `POST /auth/password/reset/request`<br>`POST /auth/login` | PARTIAL | Request acceptance is not proof of delivery; MFA provider/delivery configuration remains external. |
| Registration<br>modules/auth/RegisterPage.tsx | Account provisioning | MOCK_TO_REPLACE -> BACKEND_NOT_AVAILABLE | None | NO_BACKEND_ENDPOINT | No public registration API. Shows contact-administrator notice; no credential collection or simulated submission. |
| Facility directory and geography<br>modules/facilities/FacilitiesPage.tsx; hooks/useFacilityDirectory.ts | Metadata, hierarchy, type, status, coordinates, details | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /facilities`<br>`GET /facilities/{identifier}`<br>`GET /geography/{kind}` | CONNECTED | Active/inactive, state/district/block, type and search filters use real records; missing/pending geography distinguished. |
| Resource map<br>modules/map/InteractiveResourceMap.tsx | Facility markers and geography filters | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /facilities`<br>`GET /geography/{kind}` | PARTIAL | Only recorded coordinates plotted; missing coordinates counted. No fabricated risk coloring, heatmaps or oxygen estimates. |
| National dashboard<br>modules/dashboard/NationalDashboardPage.tsx; BackendDashboard.tsx | Facility/alert/order counts, beds, selected-facility resources | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /facilities`<br>`GET /alerts`<br>`GET /purchase-orders`<br>`GET /reports/{kind}`<br>`GET /inventory`<br>`GET /assets/{kind}`<br>`GET /operations/{kind}` | PARTIAL | Independent cards; complete directory counts, actual bed ratios. No national runway, resilience or forecast scores. |
| State dashboard<br>modules/dashboard/StateDashboardPage.tsx; BackendDashboard.tsx | Permitted-scope operational summaries | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /facilities`<br>`GET /alerts`<br>`GET /reports/{kind}`<br>`GET /operations/{kind}` | PARTIAL | No fabricated assigned state, trends or district rankings; scope is enforced by server. |
| District dashboard<br>modules/dashboard/DistrictDashboardPage.tsx; BackendDashboard.tsx | Permitted-scope operational summaries | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /facilities`<br>`GET /alerts`<br>`GET /reports/{kind}`<br>`GET /operations/{kind}` | PARTIAL | No invented district, counts or utilization values. |
| Facility dashboard<br>modules/dashboard/FacilityDashboardPage.tsx; BackendDashboard.tsx | Selected facility resources, beds and footfall | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /inventory`<br>`GET /assets/{kind}`<br>`GET /operations/{kind}`<br>`GET /reports/{kind}` | PARTIAL | Explicit facility selection; no invented hospital identity, hourly census or oxygen buffer. |
| Regional dashboard<br>modules/dashboard/RegionalDashboard.tsx; BackendDashboard.tsx | Facility drilldown and reports | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /facilities`<br>`GET /reports/{kind}` | PARTIAL | Real scope and facility selection; synthetic inter-district scorecards removed. Geographic filtering also available in directory and reports. |
| Super-admin and administration<br>modules/dashboard/SuperAdminDashboardPage.tsx; modules/admin/AdminPage.tsx | Users, roles, permissions, audit, public config and backup status | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /users`<br>`GET /roles`<br>`GET /permissions`<br>`GET /audit-logs`<br>`GET /admin/config`<br>`GET /admin/backups/status`<br>`GET /health` | CONNECTED | Read-only. No fake user creation, node key rotation, connection-pool/cache/FedML metrics. Role list backend caps at 200. |
| Medicine and stock ledger<br>modules/inventory/InventoryPage.tsx | Catalogue, facility batches, balances and movements | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /medicines`<br>`GET /inventory`<br>`GET /inventory/transactions` | CONNECTED | Joined via medicine_id. Reservations visible; unreserved stock explicitly not issue eligibility. Receive/issue/transfer deferred. |
| Expiry, DOS and safety stock<br>modules/inventory/InventoryPage.tsx | Configured expiry warnings, history status, safety/reorder quantities | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /inventory/expiry`<br>`GET /inventory/days-of-stock` | CONNECTED | Omits days override; backend policy controls expiry window. Null DOS/reorder projections remain unavailable; no-history not interpreted as safe. |
| Batch traceability and recalls<br>modules/inventory/BatchTracePanel.tsx; InventoryPage.tsx | Lot metadata, scoped stock locations, transactions, recall register | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /batches/{identifier}/trace`<br>`GET /recalls` | CONNECTED | Explicit trace pagination; no fake cold-chain rack location. Recall write workflows deferred. |
| Barcode lookup<br>modules/inventory/InventoryPage.tsx | Registered medicine/batch barcode | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /barcodes/lookup` | PARTIAL | Manual lookup is real; unknown code returns 404. Camera capture/decoding is explicitly unavailable. |
| Cold chain<br>modules/inventory/ColdChainPanel.tsx | Recorded observations and dated temperature series | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /operations/{kind}`<br>`GET /cold-chain/series` | CONNECTED | Facility scope; UTC start/end. Standard PostgreSQL series works without claiming Timescale hypertable verification. |
| Alerts<br>modules/alerts/AlertsPage.tsx | Incidents, severity, state and acknowledgement | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /alerts`<br>`POST /alerts/{identifier}/actions` | CONNECTED | Backend kinds/statuses unchanged. Existing acknowledgement uses alerts.manage and re-fetches after success. No new Phase 4 transitions. |
| Threshold and escalation rules<br>modules/alerts/AlertsPage.tsx | Thresholds, windows, escalation rules/history | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /alert-rules`<br>`GET /escalation-rules`<br>`GET /alerts/{identifier}/escalations` | CONNECTED | Read-only configured records; no local-only rule saves or fake evaluation success. |
| Notifications<br>modules/alerts/AlertsPage.tsx | Recipient delivery logs | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /notifications` | CONNECTED | Recipient and facility scope; statuses, attempts, failure reasons and delivered timestamps are actual records. |
| Warehouses<br>modules/facilities/WarehouseDashboardPage.tsx | Facility linkage, capacity metadata and stock | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /warehouses`<br>`GET /warehouses/{identifier}/inventory` | PARTIAL | No invented pallet utilization, cold-volume ratios or dispatch counts. Capacity object shown as stored. |
| Suppliers<br>modules/facilities/WarehouseDashboardPage.tsx | Supplier directory and metrics | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /suppliers`<br>`GET /suppliers/{identifier}/metrics` | CONNECTED | Metrics require global scope; null fulfilment/delay values not replaced. |
| Procurement and shipments<br>modules/facilities/WarehouseDashboardPage.tsx | Orders, items, shipment status and history | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /purchase-orders`<br>`GET /purchase-orders/{identifier}`<br>`GET /shipments`<br>`GET /shipments/{identifier}/history` | CONNECTED | Read-only; no simulated approvals, deliveries, driver identities or ETAs. |
| Transfers<br>modules/facilities/WarehouseDashboardPage.tsx | Transfer listing, items and tracking | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /transfers`<br>`GET /transfers/{identifier}` | CONNECTED | Both source and destination must be in scope. Creation/dispatch/receipt deferred to Phase 4. |
| Beds<br>modules/beds/BedsPage.tsx | Capacity, occupied, available and history | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /operations/{kind}`<br>`GET /beds/{identifier}/history` | PARTIAL | Percentages derived from recorded capacity; zero capacity not treated as 0% occupancy. No individual reservation endpoint. |
| Workforce<br>modules/workforce/WorkforcePage.tsx | Personnel, staff roles, shifts and attendance | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /operations/{kind}`<br>`GET /staff-roles` | PARTIAL | No invented department/phone/patient load, biometric evidence, paging, WHO-derived local ratios or on-duty assumptions. |
| Equipment, maintenance and ambulances<br>modules/equipment/EquipmentPage.tsx | Assets, operational state, maintenance dates/history, coordinates | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /assets/{kind}`<br>`GET /equipment/{identifier}/maintenance` | PARTIAL | Backend enum values shown exactly; no uptime percentages, crew, oxygen, ETA or fake engineer/vehicle dispatch. |
| Patient footfall<br>modules/patients/PatientsPage.tsx | Daily category counts | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /operations/{kind}` | PARTIAL | Daily aggregate records only; hourly admissions/discharges, triage and waiting times unavailable. |
| Disease surveillance<br>modules/disease/DiseasePage.tsx | Daily disease-category counts | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /operations/{kind}` | PARTIAL | No inferred outbreak risk, growth, containment radius or hotspot polygons. |
| Reports<br>modules/analytics/ReportsPanel.tsx | Report parameters/results and downloadable outputs; existing job status/download | MOCK_TO_REPLACE -> REAL_BACKEND | `GET /reports/{kind}`<br>`GET /report-jobs/{identifier}`<br>`GET /report-jobs/{identifier}/download` | CONNECTED | Seven report kinds; JSON/CSV/PDF/XLSX. Current-page exports labeled; job lookup uses known ID since no list endpoint exists. Job creation/scheduling deferred. |
| Analytics<br>modules/analytics/AIDashboard.tsx | Recorded consumption and submitted recommendations | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /datasets/medicine-consumption`<br>`GET /optimization/recommendations` | PARTIAL | Forecast, SHAP, savings, resilience and district benchmarking tabs state unavailable; no fake charts. |
| Weather/population/optimization context<br>modules/analytics/OperationalContext.tsx | Provider weather, population provenance, stock context | REAL_BACKEND + BACKEND_NOT_AVAILABLE | `GET /integrations/weather/{facility_id}`<br>`GET /integrations/population`<br>`GET /optimization/context` | PARTIAL | Weather provider is unconfigured: visible 503. Population requires district. Null prediction/transport metadata remains unavailable. |
| Emergency command<br>modules/emergency/EmergencyPage.tsx | Critical-alert reports; crisis control and scenarios | MOCK_TO_REPLACE -> REAL_BACKEND; BACKEND_NOT_AVAILABLE | `GET /reports/{kind}` | PARTIAL | Emergency report is real. Crisis toggles, polygons, vulnerability matrix, scenario solver and convoy mobilization have no configured API. |
| Federated AI<br>modules/federated-ai/FederatedAIPage.tsx | Nodes, training rounds, accuracy, privacy expenditure | MOCK_TO_REPLACE -> BACKEND_NOT_AVAILABLE | None | NO_BACKEND_ENDPOINT | No working configured backend source; all four panels show unavailable; no simulated training. |
| Settings<br>modules/auth/SettingsPage.tsx; store/uiStore.ts | Theme and public configuration | FRONTEND_ONLY + REAL_BACKEND | `GET /admin/config` | PARTIAL | Browser theme is local; enhanced-contrast/audio/offline-frequency controls disabled; no synchronization claim. |
| Offline queue<br>components/common/OfflineIndicator.tsx; utils/offlineStorage.ts | Network hint and preserved local queue | FRONTEND_ONLY | None | PARTIAL | No automatic upload implemented. Disabled Sync unavailable never clears pending records; browser online is not backend health. |
| Legacy unused demonstrations<br>pages/HomePage.tsx; components/common/TopBar.tsx; Header.tsx; services/mockData.ts; layouts/AppShell.tsx; RootLayout.tsx | Unused mock KPI datasets, simulated roles and online decoration | MOCK_TO_REPLACE (not reachable from current router) | None | MOCK | Preserved legacy source is not imported by the active main/App/router dependency graph. Must not be mounted as production data later. |
| Static reference and browser UI<br>config/*; types/*; i18n/*; components/ui/*; app/roleRoutes.ts; Navbar.tsx; Sidebar.tsx; hooks/useToast.ts | Labels, route definitions, icons, translations, theme and toast timing | STATIC_REFERENCE + FRONTEND_ONLY | None | NOT_APPLICABLE | Legitimate static references retained; role constants never create backend grants. UI timeout is not simulated backend latency. |
| Explicit placeholders<br>pages/PlaceholderPage.tsx; components/maps/PlaceholderMap.tsx; components/charts/PlaceholderChart.tsx; empty module index.ts files | Unused scaffolding | FRONTEND_ONLY | None | NOT_APPLICABLE | Explicit placeholder text only; not claimed as connected or mounted by current router. |

## Exact API contracts

Every endpoint below is used through the existing Phase 1 authenticated client, except public authentication and health calls. JSON success is `{success:true,data:...}` except the bare login token pair and health. Binary downloads use the same token/refresh path. `*` marks a required parameter; omitted filters are not sent.

| HTTP endpoint | Authentication | Permission / scope | Request schema and parameters | Response schema |
| --- | --- | --- | --- | --- |
| `GET /api/v1/health` | Public | Public; Rate/security rules apply | None | 200 application/json: HealthResponse |
| `POST /api/v1/auth/login` | Public | Public; Rate/security rules apply | application/x-www-form-urlencoded: Body_login_api_v1_auth_login_post | 200 application/json: TokenPair |
| `GET /api/v1/facilities` | Bearer JWT | inventory.read; Backend facility scope | query offset: integer default=0; query limit: integer default=50; query search: string or null; query block_id: uuid or null; query district_id: uuid or null; query state_id: uuid or null; query country_id: uuid or null; query active: boolean or null default=True | 200 application/json: Success[list[FacilityView]] |
| `GET /api/v1/medicines` | Bearer JWT | inventory.read; Shared catalogue; geography/recall listing is not facility-filtered by this backend | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[MedicineView]] |
| `GET /api/v1/inventory` | Bearer JWT | inventory.read; Backend facility scope | query facility_id*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[InventoryWithBatch]] |
| `GET /api/v1/inventory/transactions` | Bearer JWT | inventory.read; Backend facility scope | query facility_id*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[StockTransactionView]] |
| `GET /api/v1/users/me` | Bearer JWT | Signed-in user; Own identity/session | None | 200 application/json: Success[CurrentUserView] |
| `POST /api/v1/auth/refresh` | Public | Public; Rate/security rules apply | application/json: RefreshInput | 200 application/json: Success[TokenPair] |
| `POST /api/v1/auth/logout` | Bearer JWT | Signed-in user; Own identity/session | None | 200 application/json: Success[NoneType] |
| `POST /api/v1/auth/password/reset/request` | Public | Public; Rate/security rules apply | application/json: ResetRequest | 202 application/json: Success[Message] |
| `GET /api/v1/users` | Bearer JWT | admin.users; Global scope required | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[UserView]] |
| `GET /api/v1/roles` | Bearer JWT | admin.users; Global scope required | None | 200 application/json: Success[list[RoleView]] |
| `GET /api/v1/permissions` | Bearer JWT | admin.users; Global scope required | None | 200 application/json: Success[list[PermissionView]] |
| `GET /api/v1/audit-logs` | Bearer JWT | audit.read; Global scope required | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[AuditLogView]] |
| `GET /api/v1/admin/config` | Bearer JWT | admin.config; Global scope required | None | 200 application/json: Success[PublicConfig] |
| `GET /api/v1/geography/{kind}` | Bearer JWT | inventory.read; Shared catalogue; geography/recall listing is not facility-filtered by this backend | path kind*: countries/states/districts/blocks; query parent_id: uuid or null; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[Union[CountryView, StateView, DistrictView, BlockView]]] |
| `GET /api/v1/facilities/{identifier}` | Bearer JWT | inventory.read; Backend facility scope | path identifier*: uuid | 200 application/json: Success[FacilityView] |
| `GET /api/v1/inventory/days-of-stock` | Bearer JWT | inventory.read; Backend facility scope | query facility_id*: uuid; query medicine_id*: uuid; query window: integer default=30 | 200 application/json: Success[DaysOfStock] |
| `GET /api/v1/inventory/expiry` | Bearer JWT | inventory.read; Backend facility scope | query facility_id*: uuid; query days: integer or null; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[Expiry]] |
| `GET /api/v1/recalls` | Bearer JWT | inventory.read; Shared catalogue; geography/recall listing is not facility-filtered by this backend | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[RecallRecordView]] |
| `GET /api/v1/batches/{identifier}/trace` | Bearer JWT | inventory.read; Backend facility scope | path identifier*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[Trace] |
| `GET /api/v1/transfers` | Bearer JWT | inventory.read; Both source and destination facilities | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[TransferRequestView]] |
| `GET /api/v1/transfers/{identifier}` | Bearer JWT | inventory.read; Both source and destination facilities | path identifier*: uuid | 200 application/json: Success[TransferDetail] |
| `GET /api/v1/suppliers` | Bearer JWT | procurement.read; Shared supplier catalogue | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[SupplierView]] |
| `GET /api/v1/suppliers/{identifier}/metrics` | Bearer JWT | procurement.read; Global scope required | path identifier*: uuid | 200 application/json: Success[SupplierMetrics] |
| `GET /api/v1/warehouses` | Bearer JWT | inventory.read; Backend facility scope | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[WarehouseView]] |
| `GET /api/v1/warehouses/{identifier}/inventory` | Bearer JWT | inventory.read; Backend facility scope | path identifier*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[InventoryView]] |
| `GET /api/v1/purchase-orders` | Bearer JWT | procurement.read; Facility scope; transfer-linked shipments require both endpoints | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[PurchaseOrderView]] |
| `GET /api/v1/purchase-orders/{identifier}` | Bearer JWT | procurement.read; Facility scope; transfer-linked shipments require both endpoints | path identifier*: uuid | 200 application/json: Success[OrderDetail] |
| `GET /api/v1/shipments` | Bearer JWT | procurement.read; Facility scope; transfer-linked shipments require both endpoints | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[ShipmentView]] |
| `GET /api/v1/shipments/{identifier}/history` | Bearer JWT | procurement.read; Facility scope; transfer-linked shipments require both endpoints | path identifier*: uuid | 200 application/json: Success[list[ShipmentHistoryView]] |
| `GET /api/v1/beds/{identifier}/history` | Bearer JWT | beds.read; Bed facility | path identifier*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[BedOccupancyHistoryView]] |
| `GET /api/v1/staff-roles` | Bearer JWT | workforce.read; Shared staff-role catalogue | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[StaffRoleView]] |
| `GET /api/v1/operations/{kind}` | Bearer JWT | beds.read / workforce.read / integration.read / inventory.read by kind; Facility scope; no inventory grant needed for beds/workforce/aggregates | path kind*: temperatures/beds/staff/shifts/attendance/footfall/disease-counts; query facility_id*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[Union[TemperatureObservationView, BedsAvailable, StaffView, ShiftView, AttendanceView, PatientFootfallView, DiseaseCountView]]] |
| `GET /api/v1/cold-chain/series` | Bearer JWT | inventory.read; Facility scope | query facility_id*: uuid; query start*: date-time; query end*: date-time; query offset: integer default=0; query limit: integer default=200 | 200 application/json: Success[list[ColdChainSampleView]] |
| `GET /api/v1/alert-rules` | Bearer JWT | alerts.read; Facility scope | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[AlertRuleView]] |
| `GET /api/v1/alerts` | Bearer JWT | alerts.read; Facility scope | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[AlertView]] |
| `POST /api/v1/alerts/{identifier}/actions` | Bearer JWT | alerts.manage; Facility scope; backend validates transition | path identifier*: uuid; application/json: AlertAction | 200 application/json: Success[AlertView] |
| `GET /api/v1/escalation-rules` | Bearer JWT | alerts.read; Facility scope | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[EscalationRuleView]] |
| `GET /api/v1/notifications` | Bearer JWT | Signed-in user; Recipient ID plus facility scope | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[NotificationLogView]] |
| `GET /api/v1/alerts/{identifier}/escalations` | Bearer JWT | alerts.read; Facility scope | path identifier*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[EscalationHistoryView]] |
| `GET /api/v1/equipment/{identifier}/maintenance` | Bearer JWT | equipment.read; Asset facility | path identifier*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[MaintenanceRecordView]] |
| `GET /api/v1/assets/{kind}` | Bearer JWT | equipment.read; Asset facility | path kind*: equipment/ambulances; query facility_id*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[Union[EquipmentView, AmbulanceView]]] |
| `GET /api/v1/reports/{kind}` | Bearer JWT | reports.read; reports.export for binary; workforce.read for staff; Backend scope on report rows; transfer scope checks both facilities | path kind*: stock/expiry/transfers/procurement/staff/beds/emergency; query format: json/csv/xlsx/pdf default=json; query facility_id: uuid or null; query medicine_id: uuid or null; query status: string or null; query start: date-time or null; query end: date-time or null; query district_id: uuid or null; query state_id: uuid or null; query offset: integer default=0; query limit: integer default=100 | 200 application/json: Success[ReportResult]; 200 text/csv: binary; 200 application/pdf: binary; 200 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet: binary |
| `GET /api/v1/datasets/medicine-consumption` | Bearer JWT | integration.read; Facility/district scope; context also calls stock service without granting new permissions | query facility_id*: uuid; query medicine_id*: uuid; query start_date*: date; query end_date*: date; query offset: integer default=0; query limit: integer default=200 | 200 application/json: Success[list[Consumption]] |
| `GET /api/v1/optimization/context` | Bearer JWT | integration.read; Facility/district scope; context also calls stock service without granting new permissions | query facility_id*: uuid; query medicine_id*: uuid | 200 application/json: Success[OptimizationContext] |
| `GET /api/v1/optimization/recommendations` | Bearer JWT | integration.read; Facility/district scope; context also calls stock service without granting new permissions | query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[RecommendationView]] |
| `GET /api/v1/integrations/weather/{facility_id}` | Bearer JWT | integration.read; Facility/district scope; context also calls stock service without granting new permissions | path facility_id*: uuid | 200 application/json: Success[Weather] |
| `GET /api/v1/integrations/population` | Bearer JWT | integration.read; Facility/district scope; context also calls stock service without granting new permissions | query district_id*: uuid; query offset: integer default=0; query limit: integer default=50 | 200 application/json: Success[list[PopulationSnapshotView]] |
| `GET /api/v1/barcodes/lookup` | Bearer JWT | inventory.read; Shared catalogue; geography/recall listing is not facility-filtered by this backend | query code*: string | 200 application/json: Success[BarcodeView] |
| `GET /api/v1/admin/backups/status` | Bearer JWT | admin.config; Global scope required | None | 200 application/json: Success[BackupStatus] |
| `GET /api/v1/report-jobs/{identifier}` | Bearer JWT | reports.export plus report-kind authorization; Job owner and current facility scope | path identifier*: uuid | 200 application/json: Success[ReportJobView] |
| `GET /api/v1/report-jobs/{identifier}/download` | Bearer JWT | reports.export plus report-kind authorization; Job owner and current facility scope | path identifier*: uuid | 200 text/csv: binary; 200 application/pdf: binary; 200 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet: binary |

## Permission and contract mismatches

- `/facilities`, facility details and `/geography/{kind}` require `inventory.read`. This was discovered in the actual routers and remains unchanged. Directory/map links require that grant. A beds/workforce/equipment/integration-only user gets a facility-ID selector prefilled from their actual assigned IDs, instead of an unauthorized directory request. Users with district/global scope but no inventory grant must supply a permitted facility UUID. The backend still rejects out-of-scope IDs; no inventory permission is granted.
- Warehouse and transfer reads require `inventory.read`, while supplier/order/shipment reads require `procurement.read`. Warehouse navigation permits either capability, but each panel checks its own requirement independently. Supplier metrics additionally require global scope.
- Geography is a shared reference catalogue, not a user-specific list of authorized jurisdictions; facility results remain scoped. Empty results for a valid filter are not proof that an ID is authorized.
- Report JSON needs `reports.read`; binary exports need `reports.export` too; staff reports require `workforce.read`. Job status/download require `reports.export`, ownership and report-kind authorization, unlike synchronous JSON reports.
- There is no report-job listing endpoint. The UI accepts an existing job ID; it does not fabricate a completed job.
- List APIs usually return arrays without totals or has-more metadata. Tables page explicitly; complete-directory/count readers traverse pages and fail visibly at 20,000 records rather than showing a truncated total. Reports use their actual `has_more`. Batch traces page both returned sections.
- Medicine units are in the catalogue; batch IDs, facility IDs and staff-role IDs are displayed where no authorized label lookup is available. Frontend code never substitutes invented personal or geographic details.
- Coordinates may be null. There is no risk field, stockout probability, oxygen runway, crisis polygon, crew/ETA or federated-training telemetry in these response contracts.

## Backend operations without frontend coverage

These are not claimed as integrated. Most are Phase 4 mutations or machine-to-machine contracts. Alternate read endpoints can overlap data already displayed through another API. Seed-script calls do not count as frontend coverage.

| Endpoint | Reason |
| --- | --- |
| `DELETE /report-schedules/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `DELETE /roles/{identifier}/permissions/{permission_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `DELETE /users/{identifier}/districts/{district_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `DELETE /users/{identifier}/facilities/{facility_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `DELETE /users/{identifier}/roles/{role_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `GET /` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `GET /auth/me` | Superseded in frontend by richer /users/me contract |
| `GET /datasets/{kind}` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `GET /facilities/nearby` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `GET /integrations/fhir/locations/{identifier}` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `GET /medicines/{identifier}` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `GET /sync/pull` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `GET /users/{identifier}` | No frontend caller; alternate, infrastructure or machine-to-machine read |
| `PATCH /facilities/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PATCH /medicines/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PATCH /users/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /admin/backups` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /alert-rules` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /alert-rules/{identifier}/evaluate` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /ambulances` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /attendance` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /auth/password/change` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /auth/password/reset/confirm` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /barcodes` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /cold-chain/observations` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /equipment` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /equipment/{identifier}/maintenance` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /escalation-rules` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /facilities` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /geography/{kind}` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /integrations/population` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /inventory/adjust` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /inventory/issue` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /inventory/receive` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /medicines` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /notifications/{identifier}/retry` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /optimization/recommendations` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /optimization/recommendations/{identifier}/actions` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /purchase-orders` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /purchase-orders/{identifier}/actions` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /purchase-orders/{identifier}/receive` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /recalls` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /recalls/{identifier}/resolve` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /report-jobs` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /report-schedules` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /roles` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /shifts` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /shifts/{identifier}/cancel` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /shipments` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /shipments/{identifier}/actions` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /staff` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /staff-roles` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /suppliers` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /sync/push` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /transfers` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /transfers/{identifier}/actions` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /users` | Phase 4 mutation / administrative or integration workflow deferred |
| `POST /warehouses` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /aggregates/{kind}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /alert-rules/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /ambulances/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /beds` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /equipment/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /escalation-rules/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /inventory/policies/{facility_id}/{medicine_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /roles/{identifier}/permissions/{permission_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /staff/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /suppliers/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /users/{identifier}/districts/{district_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /users/{identifier}/facilities/{facility_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /users/{identifier}/roles/{role_id}` | Phase 4 mutation / administrative or integration workflow deferred |
| `PUT /warehouses/{identifier}` | Phase 4 mutation / administrative or integration workflow deferred |

## Application source inventory

All TypeScript/TSX source files were inventoried. Unit-test response fixtures live only under `src/test`; they are not production fallback data. The logical-area table above supplies the detailed contracts for each module.

| Source | Source category / role |
| --- | --- |
| `app/App.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `app/authorization.ts` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `app/navigationConfig.ts` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `app/roleRoutes.ts` | STATIC_REFERENCE |
| `app/router.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/charts/PlaceholderChart.tsx` | FRONTEND_ONLY scaffolding / module exports |
| `components/common/BackendData.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/CommandPalette.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/FacilityPicker.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/Header.tsx` | MOCK_TO_REPLACE: legacy, not active router dependency |
| `components/common/Navbar.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/OfflineIndicator.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/PermissionGuard.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/ProtectedRoute.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/RoleGuard.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/RoleSidebar.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/RoleTopBar.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/Sidebar.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `components/common/TopBar.tsx` | MOCK_TO_REPLACE: legacy, not active router dependency |
| `components/maps/PlaceholderMap.tsx` | FRONTEND_ONLY scaffolding / module exports |
| `components/ui/Badge.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/Card.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/EmptyState.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/ErrorState.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/LoadingScreen.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/Modal.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/Toast.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `components/ui/ToastContainer.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `hooks/useBackendData.ts` | REAL_BACKEND contract / transport / authenticated state |
| `hooks/useFacilityDirectory.ts` | REAL_BACKEND contract / transport / authenticated state |
| `hooks/useHealth.ts` | REAL_BACKEND public liveness; not dependency readiness |
| `hooks/useToast.ts` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `i18n/index.ts` | STATIC_REFERENCE |
| `layouts/AdminLayout.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/AppShell.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/DistrictLayout.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/FacilityLayout.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/NationalLayout.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/RoleAppShell.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/RootLayout.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `layouts/StateLayout.tsx` | FRONTEND_ONLY presentation; no operational dataset |
| `main.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `modules/admin/AdminPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/admin/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/alerts/AlertsPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/analytics/AIDashboard.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/analytics/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/analytics/OperationalContext.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/analytics/ReportsPanel.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/auth/ForgotPasswordPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/auth/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/auth/LoginPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/auth/MFAPage.tsx` | BACKEND_NOT_AVAILABLE notice / external verification boundary |
| `modules/auth/ProfilePage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/auth/RegisterPage.tsx` | BACKEND_NOT_AVAILABLE notice / external verification boundary |
| `modules/auth/SettingsPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/beds/BedsPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/beds/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/dashboard/BackendDashboard.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/dashboard/DistrictDashboardPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/dashboard/FacilityDashboardPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/dashboard/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/dashboard/NationalDashboardPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/dashboard/RegionalDashboard.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/dashboard/StateDashboardPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/dashboard/SuperAdminDashboardPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/disease/DiseasePage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/disease/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/emergency/EmergencyPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/emergency/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/equipment/EquipmentPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/equipment/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/facilities/FacilitiesPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/facilities/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/facilities/WarehouseDashboardPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/federated-ai/FederatedAIPage.tsx` | BACKEND_NOT_AVAILABLE notice / external verification boundary |
| `modules/federated-ai/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/inventory/BatchTracePanel.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/inventory/ColdChainPanel.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/inventory/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/inventory/InventoryPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/map/InteractiveResourceMap.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/patients/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/patients/PatientsPage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `modules/procurement/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/workforce/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `modules/workforce/WorkforcePage.tsx` | REAL_BACKEND consumer; unsupported values explicitly BACKEND_NOT_AVAILABLE |
| `pages/HomePage.tsx` | MOCK_TO_REPLACE: legacy, not active router dependency |
| `pages/PlaceholderPage.tsx` | FRONTEND_ONLY scaffolding / module exports |
| `pages/UnauthorizedPage.tsx` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `services/api.ts` | REAL_BACKEND contract / transport / authenticated state |
| `services/authService.ts` | REAL_BACKEND contract / transport / authenticated state |
| `services/backendTypes.ts` | REAL_BACKEND contract / transport / authenticated state |
| `services/dataApi.ts` | REAL_BACKEND contract / transport / authenticated state |
| `services/httpClient.ts` | REAL_BACKEND contract / transport / authenticated state |
| `services/mockData.ts` | MOCK_TO_REPLACE: legacy, not active router dependency |
| `store/authStore.ts` | REAL_BACKEND contract / transport / authenticated state |
| `store/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `store/uiStore.ts` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `types/auth.ts` | STATIC_REFERENCE |
| `types/index.ts` | STATIC_REFERENCE |
| `utils/index.ts` | FRONTEND_ONLY scaffolding / module exports |
| `utils/offlineStorage.ts` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |
| `vite-env.d.ts` | FRONTEND_ONLY / STATIC_REFERENCE; permission-aware consumers use actual auth state |

## Counts

- 39 logical frontend areas; 104 application TypeScript/TSX source files.
- 33 areas have at least one real API integration (includes PARTIAL rows).
- Status counts: {"CONNECTED": 15, "MOCK": 1, "NOT_APPLICABLE": 2, "NO_BACKEND_ENDPOINT": 2, "PARTIAL": 19}.
- 53 of 125 OpenAPI operations have frontend callers; 72 have no caller, including 8 GET operations. Read coverage is not mutation coverage.

## Phase 4 mutation addendum

Updated 2026-10-02. The [complete mutation matrix](PHASE4_MUTATION_MATRIX.md) contains all 169 control declarations, request schemas, permissions, state rules, idempotency, audit and refetch behavior. The [Phase 4 report](PHASE4_OPERATIONAL_INTEGRATION.md) separates implemented controls from the five actually executed live chains.

Current combined coverage: **84/125 operations**, with **33 non-GET and 8 GET operations** without a frontend caller. Phase 4 added 31 operations; alert acknowledgement was already connected and resolution shares that endpoint. No omitted operation is automatically a requirement for a new UI control.

| Current action | Method / endpoint | Status |
| --- | --- | --- |
| Receive stock | `POST /inventory/receive` | CONNECTED_MUTATION, subject to listed permissions/state |
| Issue stock | `POST /inventory/issue` | CONNECTED_MUTATION, subject to listed permissions/state |
| Adjust stock | `POST /inventory/adjust` | CONNECTED_MUTATION, subject to listed permissions/state |
| Create transfer | `POST /transfers` | CONNECTED_MUTATION, subject to listed permissions/state |
| approve transfer | `POST /transfers/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| reject transfer | `POST /transfers/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| dispatch transfer | `POST /transfers/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| in_transit transfer | `POST /transfers/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| receive transfer | `POST /transfers/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| cancel transfer | `POST /transfers/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Create supplier | `POST /suppliers` | CONNECTED_MUTATION, subject to listed permissions/state |
| Edit supplier | `PUT /suppliers/{identifier}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Register warehouse | `POST /warehouses` | CONNECTED_MUTATION, subject to listed permissions/state |
| Edit warehouse | `PUT /warehouses/{identifier}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Create purchase order | `POST /purchase-orders` | CONNECTED_MUTATION, subject to listed permissions/state |
| submit order | `POST /purchase-orders/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| approve order | `POST /purchase-orders/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| order order | `POST /purchase-orders/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| cancel order | `POST /purchase-orders/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Receive purchase order | `POST /purchase-orders/{identifier}/receive` | CONNECTED_MUTATION, subject to listed permissions/state |
| Create shipment | `POST /shipments` | CONNECTED_MUTATION, subject to listed permissions/state |
| Mark shipment dispatched | `POST /shipments/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Mark shipment in_transit | `POST /shipments/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Mark shipment arrived | `POST /shipments/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Mark shipment cancelled | `POST /shipments/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Update bed capacity | `PUT /beds` | CONNECTED_MUTATION, subject to listed permissions/state |
| Add staff role | `POST /staff-roles` | CONNECTED_MUTATION, subject to listed permissions/state |
| Add staff | `POST /staff` | CONNECTED_MUTATION, subject to listed permissions/state |
| Edit staff | `PUT /staff/{identifier}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Create shift | `POST /shifts` | CONNECTED_MUTATION, subject to listed permissions/state |
| Cancel shift | `POST /shifts/{identifier}/cancel` | CONNECTED_MUTATION, subject to listed permissions/state |
| Record attendance | `POST /attendance` | CONNECTED_MUTATION, subject to listed permissions/state |
| Record footfall | `PUT /aggregates/{kind}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Record disease count | `PUT /aggregates/{kind}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Register equipment | `POST /equipment` | CONNECTED_MUTATION, subject to listed permissions/state |
| Edit equipment | `PUT /equipment/{identifier}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Record maintenance | `POST /equipment/{identifier}/maintenance` | CONNECTED_MUTATION, subject to listed permissions/state |
| Register ambulance | `POST /ambulances` | CONNECTED_MUTATION, subject to listed permissions/state |
| Edit ambulance | `PUT /ambulances/{identifier}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Create facility | `POST /facilities` | CONNECTED_MUTATION, subject to listed permissions/state |
| Edit facility | `PATCH /facilities/{identifier}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Add countries | `POST /geography/{kind}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Add states | `POST /geography/{kind}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Add districts | `POST /geography/{kind}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Add blocks | `POST /geography/{kind}` | CONNECTED_MUTATION, subject to listed permissions/state |
| Acknowledge alert | `POST /alerts/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Resolve alert | `POST /alerts/{identifier}/actions` | CONNECTED_MUTATION, subject to listed permissions/state |
| Request report job | `POST /report-jobs` | CONNECTED_MUTATION, subject to listed permissions/state |

The original Phase 3 notes saying operational actions awaited Phase 4 are historical. The current matrix above supersedes those notes for connected actions; intentionally read-only and unsupported actions remain explicitly listed in the Phase 4 matrix. Backend permissions and contracts were not broadened.
