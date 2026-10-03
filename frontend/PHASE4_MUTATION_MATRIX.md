> Current status: see [Phase 5 readiness audit](../FINAL_READINESS_AUDIT.md) and [supported setup](../DEVELOPMENT.md). This report retains historical phase results. Phase 5 adds optional report-job idempotency (`ReportJobRequest`), real Celery worker/Beat verification, and explicit production API configuration. Earlier statements about those gaps are superseded.

# Phase 4 operational mutation matrix

Audited 2026-10-02 on `integration/frontend-backend`. Contract: the running FastAPI `/api/v1/openapi.json`, endpoint dependencies and service state machines. All paths below have the `/api/v1` prefix. Phases 1-3 are preserved.

## Counting and verification scope

**77 action/workflow dispositions audited:** 48 connected user actions, 13 intentionally read-only workflow families, and 16 unsupported/deferred families. Connected actions cover 32 endpoint families (31 newly covered operations plus existing alert actions). Dynamic state choices and four geography levels are counted as separate user actions; related unexposed administrative operations are grouped as named workflow families below.

These workflow counts are not live-test counts. **Five representative live mutation chains** passed, covering 12 distinct action variants: stock receive/issue/adjust, transfer create/approve/dispatch/in_transit/receive, alert acknowledge/resolve, bed update, and report-job request. Other connected controls have shared frontend contract/regression coverage and existing backend tests; they are not all individually live-certified. Report generation was invoked through the existing service under an isolated-job database guard, not an unattended Celery worker/beat deployment.

## Shared behavior and error contract

All connected forms use the existing authenticated `apiRequest` through `sendData`; no parallel fetch or mock success. Request schemas are selected verbatim from OpenAPI in `src/services/mutationSchemas.ts`; `MutationForm.tsx` renders ordinary labeled inputs, enums and line-item fields. Local validation covers required/ranged fields and relevant cross-field rules. Server validation remains authoritative.

Every row below handles authentication expiry/refresh, 400, 401, 403, 404, 409, 422, 429, 5xx and network errors via the shared client. This is a handling policy, not a claim that every endpoint emits every status. Wrong facility is deliberately 404 (`Facility not found or outside assigned scope`). 409 includes exact safe business-rule details; 422 includes field errors; 5xx is sanitized. Success appears only after a confirmed HTTP success envelope.

A synchronous submission lock and disabled pending controls prevent duplicate clicks. Supported inventory/transfer-create/order-receipt requests retain the same payload and idempotency key across uncertain retries/remounts in user-scoped session storage. Non-idempotent uncertain outcomes stop retries and instruct the operator to check records. This is not a cross-client deduplication guarantee. Independent repeated report requests create duplicate jobs; a regression documents that missing backend capability.

Every connected success invalidates the real `backend` query family, including lists, detail, stock, history and reports. Query keys remain user/scope/grant-specific. No optimistic inventory result is used. Conflicts also invalidate current reads. Report jobs additionally poll while status is `pending`. Other terminal states are the actual backend `completed`, `failed`, `expired`; `running` is not invented.

Issue, adjustment, transfer dispatch/receive/reject/cancel, order receipt/cancel, shipment transitions, bed replacement, facility/warehouse changes and selected asset/personnel changes require review of the actual payload. Transfer confirmations also identify reference, record and facilities; selected detail shows items/history. Harmless navigation and read controls do not require confirmation.

## Connected user actions

`CONNECTED_MUTATION` means implemented real request plus refresh, subject to listed permissions and prerequisites. Without permission the control is `NOT_AUTHORIZED_FOR_ROLE` (hidden); backend dependencies remain authoritative even for manual requests. Source files are relative to `frontend/src/`. Exact success envelope names/statuses below come from OpenAPI. Request schema definitions are listed after this table.

| Frontend action / source | Method / endpoint | Required permission / scope | Request schema | Success response | State transition / business rule | Idempotency | Audit implications | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Receive stock<br>`modules/inventory/InventoryActions.tsx` | POST `/inventory/receive` | inventory.write + facility scope | Receive | 201 Success_Received_ | Add usable batch stock; create/reuse matching batch | Actor + operation + idempotency_key; stable payload on uncertain retry | inventory.receive | CONNECTED_MUTATION |
| Issue stock<br>`modules/inventory/InventoryActions.tsx` | POST `/inventory/issue` | inventory.write + facility scope | Issue | 200 Success_Issued_ | FEFO usable unreserved stock -> negative ledger allocations | Actor + operation + idempotency_key; stable payload on uncertain retry | inventory.issue | CONNECTED_MUTATION |
| Adjust stock<br>`modules/inventory/InventoryActions.tsx` | POST `/inventory/adjust` | inventory.write + facility scope | Adjustment | 200 Success_Adjusted_ | Signed adjustment; reserved stock and expiry/recall rules enforced | Actor + operation + idempotency_key; stable payload on uncertain retry | inventory.adjust | CONNECTED_MUTATION |
| Create transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers` | inventory.transfer; both facilities | TransferCreate | 201 Success_TransferRequestView_ | New -> pending_approval | Actor + transfer.create + idempotency_key | transfer.requested | CONNECTED_MUTATION |
| approve transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers/{identifier}/actions` | inventory.transfer; both facilities | TransferAction | 200 Success_TransferRequestView_ | pending_approval -> approved; reserve usable stock above safety stock | State lock; repeated transition 409 (no key) | transfer.approve | CONNECTED_MUTATION |
| reject transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers/{identifier}/actions` | inventory.transfer; both facilities | TransferAction | 200 Success_TransferRequestView_ | pending_approval -> rejected | State lock; repeated transition 409 (no key) | transfer.reject | CONNECTED_MUTATION |
| dispatch transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers/{identifier}/actions` | inventory.transfer; both facilities | TransferAction | 200 Success_TransferRequestView_ | approved -> dispatched; debit source and release reservation | State lock; repeated transition 409 (no key) | transfer.dispatch | CONNECTED_MUTATION |
| in_transit transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers/{identifier}/actions` | inventory.transfer; both facilities | TransferAction | 200 Success_TransferRequestView_ | dispatched -> in_transit | State lock; repeated transition 409 (no key) | transfer.in_transit | CONNECTED_MUTATION |
| receive transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers/{identifier}/actions` | inventory.transfer; both facilities | TransferAction | 200 Success_TransferRequestView_ | dispatched/in_transit -> received; credit destination; shipments arrived/cancelled | State lock; repeated transition 409 (no key) | transfer.receive | CONNECTED_MUTATION |
| cancel transfer<br>`modules/facilities/SupplyActions.tsx` | POST `/transfers/{identifier}/actions` | inventory.transfer; both facilities | TransferAction | 200 Success_TransferRequestView_ | pending_approval/approved -> cancelled; release reservation; cancel shipments first | State lock; repeated transition 409 (no key) | transfer.cancel | CONNECTED_MUTATION |
| Create supplier<br>`modules/facilities/SupplyActions.tsx` | POST `/suppliers` | procurement.write + global | SupplierInput | 201 Success_SupplierView_ | Persist details/active status | Unique supplier code; no request key | supplier.saved | CONNECTED_MUTATION |
| Edit supplier<br>`modules/facilities/SupplyActions.tsx` | PUT `/suppliers/{identifier}` | procurement.write + global | SupplierInput | 200 Success_SupplierView_ | Persist details/active status | Unique supplier code; no request key | supplier.saved | CONNECTED_MUTATION |
| Register warehouse<br>`modules/facilities/SupplyActions.tsx` | POST `/warehouses` | facility.manage + facility scope | WarehouseInput | 201 Success_WarehouseView_ | Facility becomes warehouse; existing stock linked | Unique facility warehouse; no request key | warehouse.created | CONNECTED_MUTATION |
| Edit warehouse<br>`modules/facilities/SupplyActions.tsx` | PUT `/warehouses/{identifier}` | facility.manage + facility scope | WarehouseUpdate | 200 Success_WarehouseView_ | Capacity and parent facility active state updated together | Set-value update; no request key | warehouse.updated | CONNECTED_MUTATION |
| Create purchase order<br>`modules/facilities/SupplyActions.tsx` | POST `/purchase-orders` | procurement.write + facility scope | OrderInput | 201 Success_PurchaseOrderView_ | New -> draft; active supplier and distinct medicine lines | Unique reference, duplicate 409; no key | procurement.created | CONNECTED_MUTATION |
| submit order<br>`modules/facilities/SupplyActions.tsx` | POST `/purchase-orders/{identifier}/actions` | procurement.write + facility scope | OrderAction | 200 Success_PurchaseOrderView_ | draft -> submitted | State lock; repeated transition 409; no key | procurement.submit | CONNECTED_MUTATION |
| approve order<br>`modules/facilities/SupplyActions.tsx` | POST `/purchase-orders/{identifier}/actions` | procurement.write + procurement.approve + facility scope | OrderAction | 200 Success_PurchaseOrderView_ | submitted -> approved | State lock; repeated transition 409; no key | procurement.approve | CONNECTED_MUTATION |
| order order<br>`modules/facilities/SupplyActions.tsx` | POST `/purchase-orders/{identifier}/actions` | procurement.write + facility scope | OrderAction | 200 Success_PurchaseOrderView_ | approved -> ordered | State lock; repeated transition 409; no key | procurement.order | CONNECTED_MUTATION |
| cancel order<br>`modules/facilities/SupplyActions.tsx` | POST `/purchase-orders/{identifier}/actions` | procurement.write + facility scope | OrderAction | 200 Success_PurchaseOrderView_ | draft/submitted/approved/ordered -> cancelled; cancel planned shipments first | State lock; repeated transition 409; no key | procurement.cancel | CONNECTED_MUTATION |
| Receive purchase order<br>`modules/facilities/SupplyActions.tsx` | POST `/purchase-orders/{identifier}/receive` | procurement.write + inventory.write + facility scope | OrderReceipt | 200 Success_OrderReceived_ | ordered/partially_received -> partially_received/received; item remainder; shipments arrived/cancelled | Actor + procurement.receive.ORDER_ID + idempotency_key | procurement.received + inventory.receive | CONNECTED_MUTATION |
| Create shipment<br>`modules/facilities/SupplyActions.tsx` | POST `/shipments` | procurement.write; both scopes for transfer source | ShipmentInput | 201 Success_ShipmentView_ | Eligible order/transfer -> planned shipment; exactly one source | Unique shipment reference; no request key | shipment.created | CONNECTED_MUTATION |
| Mark shipment dispatched<br>`modules/facilities/SupplyActions.tsx` | POST `/shipments/{identifier}/actions` | procurement.write; both scopes for transfer source | ShipmentAction | 200 Success_ShipmentView_ | planned -> dispatched; parent state also checked | State lock; repeated transition 409; no key | shipment.dispatched | CONNECTED_MUTATION |
| Mark shipment in_transit<br>`modules/facilities/SupplyActions.tsx` | POST `/shipments/{identifier}/actions` | procurement.write; both scopes for transfer source | ShipmentAction | 200 Success_ShipmentView_ | dispatched -> in_transit; parent state also checked | State lock; repeated transition 409; no key | shipment.in_transit | CONNECTED_MUTATION |
| Mark shipment arrived<br>`modules/facilities/SupplyActions.tsx` | POST `/shipments/{identifier}/actions` | procurement.write; both scopes for transfer source | ShipmentAction | 200 Success_ShipmentView_ | dispatched/in_transit -> arrived; parent state also checked | State lock; repeated transition 409; no key | shipment.arrived | CONNECTED_MUTATION |
| Mark shipment cancelled<br>`modules/facilities/SupplyActions.tsx` | POST `/shipments/{identifier}/actions` | procurement.write; both scopes for transfer source | ShipmentAction | 200 Success_ShipmentView_ | planned -> cancelled; parent state also checked | State lock; repeated transition 409; no key | shipment.cancelled | CONNECTED_MUTATION |
| Update bed capacity<br>`modules/equipment/OperationsActions.tsx` | PUT `/beds` | beds.write + facility scope | BedInput | 200 Success_BedsAvailable_ | Replace capacity/occupied by facility + bed type; occupied <= capacity | Same values preserve balance; each save has history/audit; no key | beds.updated | CONNECTED_MUTATION |
| Add staff role<br>`modules/equipment/OperationsActions.tsx` | POST `/staff-roles` | workforce.write + global | StaffRoleInput | 201 Success_StaffRoleView_ | Create staff role | No request key; domain uniqueness/conflict rules only | staff_role.created | CONNECTED_MUTATION |
| Add staff<br>`modules/equipment/OperationsActions.tsx` | POST `/staff` | workforce.write + facility scope | StaffInput | 201 Success_StaffView_ | Create staff with real role | No request key; domain uniqueness/conflict rules only | staff.saved | CONNECTED_MUTATION |
| Edit staff<br>`modules/equipment/OperationsActions.tsx` | PUT `/staff/{identifier}` | workforce.write + facility scope | StaffInput | 200 Success_StaffView_ | Update staff details/active flag | No request key; domain uniqueness/conflict rules only | staff.saved | CONNECTED_MUTATION |
| Create shift<br>`modules/equipment/OperationsActions.tsx` | POST `/shifts` | workforce.write + staff facility scope | ShiftInput | 201 Success_ShiftView_ | Active staff; nonoverlapping shift <=24h | No request key; domain uniqueness/conflict rules only | shift.created | CONNECTED_MUTATION |
| Cancel shift<br>`modules/equipment/OperationsActions.tsx` | POST `/shifts/{identifier}/cancel` | workforce.write + shift facility scope | None | 200 Success_ShiftView_ | Not cancelled -> cancelled | No request key; domain uniqueness/conflict rules only | shift.cancelled | CONNECTED_MUTATION |
| Record attendance<br>`modules/equipment/OperationsActions.tsx` | POST `/attendance` | workforce.write + staff facility scope | AttendanceInput | 201 Success_AttendanceView_ | One present/absent/leave entry per staff/day | No request key; domain uniqueness/conflict rules only | attendance.recorded | CONNECTED_MUTATION |
| Record footfall<br>`modules/equipment/OperationsActions.tsx` | PUT `/aggregates/{kind}` | integration.write + facility scope | AggregateInput | 200 Success_Union_PatientFootfallView__DiseaseCountView__ | kind=footfall; expected_version match -> next version | Optimistic expected_version; repeated stale update 409 | footfall.recorded | CONNECTED_MUTATION |
| Record disease count<br>`modules/equipment/OperationsActions.tsx` | PUT `/aggregates/{kind}` | integration.write + facility scope | AggregateInput | 200 Success_Union_PatientFootfallView__DiseaseCountView__ | kind=disease-counts; expected_version match -> next version | Optimistic expected_version; repeated stale update 409 | disease-counts.recorded | CONNECTED_MUTATION |
| Register equipment<br>`modules/equipment/OperationsActions.tsx` | POST `/equipment` | equipment.write + facility scope | EquipmentInput | 201 Success_EquipmentView_ | Create equipment with backend enum status | No request key; domain uniqueness/conflict rules only | equipment.saved | CONNECTED_MUTATION |
| Edit equipment<br>`modules/equipment/OperationsActions.tsx` | PUT `/equipment/{identifier}` | equipment.write + facility scope | EquipmentInput | 200 Success_EquipmentView_ | Save backend enum status and details | No request key; domain uniqueness/conflict rules only | equipment.saved | CONNECTED_MUTATION |
| Record maintenance<br>`modules/equipment/OperationsActions.tsx` | POST `/equipment/{identifier}/maintenance` | equipment.write + facility scope | MaintenanceInput | 201 Success_MaintenanceRecordView_ | Past/today UTC performed date, later next_due, no backdating latest maintenance | No key or duplicate-event deduplication; uncertain resubmission blocked in UI | equipment.maintained | CONNECTED_MUTATION |
| Register ambulance<br>`modules/equipment/OperationsActions.tsx` | POST `/ambulances` | equipment.write + facility scope | AmbulanceInput | 201 Success_AmbulanceView_ | Create availability record, paired coordinates | No request key; domain uniqueness/conflict rules only | ambulance_records.saved | CONNECTED_MUTATION |
| Edit ambulance<br>`modules/equipment/OperationsActions.tsx` | PUT `/ambulances/{identifier}` | equipment.write + facility scope | AmbulanceInput | 200 Success_AmbulanceView_ | Save enum availability; non-operational cannot be available; no dispatch semantics | No request key; domain uniqueness/conflict rules only | ambulance_records.saved | CONNECTED_MUTATION |
| Create facility<br>`modules/facilities/FacilityActions.tsx` | POST `/facilities` | facility.manage + global | FacilityCreate | 201 Success_FacilityView_ | Create basic facility; edit metadata separately | Unique facility code; no request key | facility.create | CONNECTED_MUTATION |
| Edit facility<br>`modules/facilities/FacilityActions.tsx` | PATCH `/facilities/{identifier}` | facility.manage + facility scope | FacilityUpdate | 200 Success_FacilityView_ | Update submitted metadata; active state synchronizes warehouse | Set-value update; no request key | facility.updated | CONNECTED_MUTATION |
| Add countries<br>`modules/facilities/FacilityActions.tsx` | POST `/geography/{kind}` | facility.manage + global | GeographyCreate | 201 Success_Union_CountryView__StateView__DistrictView__BlockView__ | countries creation; correct parent required except country | Unique geography code; no request key | geography.created | CONNECTED_MUTATION |
| Add states<br>`modules/facilities/FacilityActions.tsx` | POST `/geography/{kind}` | facility.manage + global | GeographyCreate | 201 Success_Union_CountryView__StateView__DistrictView__BlockView__ | states creation; correct parent required except country | Unique geography code; no request key | geography.created | CONNECTED_MUTATION |
| Add districts<br>`modules/facilities/FacilityActions.tsx` | POST `/geography/{kind}` | facility.manage + global | GeographyCreate | 201 Success_Union_CountryView__StateView__DistrictView__BlockView__ | districts creation; correct parent required except country | Unique geography code; no request key | geography.created | CONNECTED_MUTATION |
| Add blocks<br>`modules/facilities/FacilityActions.tsx` | POST `/geography/{kind}` | facility.manage + global | GeographyCreate | 201 Success_Union_CountryView__StateView__DistrictView__BlockView__ | blocks creation; correct parent required except country | Unique geography code; no request key | geography.created | CONNECTED_MUTATION |
| Acknowledge alert<br>`modules/alerts/AlertsPage.tsx` | POST `/alerts/{identifier}/actions` | alerts.manage + facility scope | AlertAction | 200 Success_AlertView_ | open -> acknowledged | State lock; repeat 409; no key | alert.acknowledged | CONNECTED_MUTATION |
| Resolve alert<br>`modules/alerts/AlertsPage.tsx` | POST `/alerts/{identifier}/actions` | alerts.manage + facility scope | AlertAction | 200 Success_AlertView_ | open/acknowledged -> resolved; clear active key | State lock; repeat 409; no key | alert.resolved | CONNECTED_MUTATION |
| Request report job<br>`modules/analytics/ReportsPanel.tsx` | POST `/report-jobs` | reports.export + reports.read + facility scope; staff adds workforce.read; transfers global | ReportRequest | 202 Success_ReportJobView_ | Create pending; poll actual pending/completed/failed/expired; no running state | NO backend deduplication; uncertain retry blocked; duplicate independent requests create jobs | report.requested; report.completed when generator runs | CONNECTED_MUTATION |

## Request schema inventory

Fields and constraints are not inferred from UI examples. `?` denotes optional; defaults and numeric/string/date constraints remain in the generated source and server schema. Fixed fields such as selected facility IDs are still included in requests. Arrays support distinct multiple line items, up to the backend limit.

| Schema | Fields |
| --- | --- |
| Adjustment | `facility_id`, `batch_id`, `quantity`, `kind?`, `reference`, `idempotency_key` |
| AggregateInput | `facility_id`, `day`, `category`, `count`, `expected_version?`, `source_device?` |
| AlertAction | `status` |
| AmbulanceInput | `facility_id`, `vehicle_id`, `status?`, `operational?`, `latitude?`, `longitude?` |
| AttendanceInput | `staff_id`, `day`, `status` |
| BedInput | `facility_id`, `bed_type`, `capacity`, `occupied` |
| EquipmentInput | `facility_id`, `code`, `equipment_type`, `status?`, `next_maintenance?`, `notes?` |
| FacilityCreate | `name`, `code` |
| FacilityUpdate | `name?`, `facility_type?`, `address?`, `block_id?`, `latitude?`, `longitude?`, `contact?`, `active?` |
| GeographyCreate | `name`, `code`, `parent_id?` |
| Issue | `idempotency_key?`, `facility_id`, `medicine_id`, `quantity`, `reference` |
| MaintenanceInput | `performed_on`, `next_due`, `notes` |
| OrderAction | `action`, `note` |
| OrderInput | `reference`, `supplier_id`, `facility_id`, `items` |
| OrderReceipt | `item_id`, `batch_number`, `expires_on`, `quantity`, `idempotency_key` |
| Receive | `idempotency_key?`, `facility_id`, `medicine_id`, `batch_number`, `expires_on`, `quantity`, `reference` |
| ReportRequest | `facility_id`, `kind`, `format?` |
| ShiftInput | `staff_id`, `starts_at`, `ends_at` |
| ShipmentAction | `status`, `note` |
| ShipmentInput | `reference`, `order_id?`, `transfer_id?`, `origin`, `expected_at`, `vehicle?`, `carrier?` |
| StaffInput | `facility_id`, `staff_role_id`, `code`, `display_name`, `active?` |
| StaffRoleInput | `name` |
| SupplierInput | `name`, `code`, `contact?`, `address?`, `lead_days?`, `active?` |
| TransferAction | `action`, `reason` |
| TransferCreate | `source_id`, `destination_id`, `reference`, `items`, `idempotency_key` |
| WarehouseInput | `facility_id`, `capacity_units?`, `cold_storage?` |
| WarehouseUpdate | `capacity_units?`, `cold_storage?`, `active?` |

## Intentionally read-only workflow families

These backend operations exist, but no dedicated user-facing workflow is introduced merely to increase API coverage. Current read panels and notices are honest; backend operations remain available to authorized existing clients.

| Workflow | Backend operations | Status | Reason |
| --- | --- | --- | --- |
| Medicine catalogue administration | POST /medicines; PATCH /medicines/{identifier} | READ_ONLY_BY_DESIGN | Inventory catalogue remains read-only; no dedicated governed medicine editor in the current UI. |
| Barcode registry administration | POST /barcodes | READ_ONLY_BY_DESIGN | Lookup is connected; registry writes have no dedicated registration workflow. |
| Stock-policy administration | PUT /inventory/policies/{facility_id}/{medicine_id} | READ_ONLY_BY_DESIGN | Read policy results; no policy approval/configuration editor introduced. |
| Global recall administration | POST /recalls; POST /recalls/{identifier}/resolve | READ_ONLY_BY_DESIGN | Recall register/trace remains readable; global batch recall and disposition need a dedicated workflow. |
| Threshold-rule administration | POST /alert-rules; PUT /alert-rules/{identifier} | READ_ONLY_BY_DESIGN | Configured rules remain readable; no generic rule editor exposed. |
| Escalation-rule administration | POST /escalation-rules; PUT /escalation-rules/{identifier} | READ_ONLY_BY_DESIGN | History/rules readable; recipient/channel governance not replaced with raw UUID forms. |
| Recurring report schedules | POST /report-schedules; DELETE /report-schedules/{identifier} | READ_ONLY_BY_DESIGN | Current UI requests individual jobs; no schedule listing endpoint or schedule-management screen. |
| Account provisioning and updates | POST /users; PATCH /users/{identifier} | READ_ONLY_BY_DESIGN | User administration remains read-only; do not mechanically expose credential/security changes. |
| Role catalogue administration | POST /roles | READ_ONLY_BY_DESIGN | Roles/permissions are readable; no new role-definition workflow. |
| Permission grant/revocation | PUT /roles/{identifier}/permissions/{permission_id}; DELETE /roles/{identifier}/permissions/{permission_id} | READ_ONLY_BY_DESIGN | Governed security administration intentionally excluded from operational forms. |
| User role assignment/revocation | PUT /users/{identifier}/roles/{role_id}; DELETE /users/{identifier}/roles/{role_id} | READ_ONLY_BY_DESIGN | Same governed administration boundary. |
| Facility/district scope assignments | PUT /users/{identifier}/facilities/{facility_id}; DELETE /users/{identifier}/facilities/{facility_id}; PUT /users/{identifier}/districts/{district_id}; DELETE /users/{identifier}/districts/{district_id} | READ_ONLY_BY_DESIGN | No scope-grant controls added to bypass directory or operational permissions. |
| Password change/reset confirmation | POST /auth/password/change; POST /auth/password/reset/confirm | READ_ONLY_BY_DESIGN | Existing Phase 1 authentication/recovery request preserved; no new password-management flow in Phase 4. |

## External/infrastructure and unsupported actions

| Workflow | Existing operation, if any | Status | Gap |
| --- | --- | --- | --- |
| Cold-chain ingestion | POST /cold-chain/observations | DEFERRED_EXTERNAL_INTEGRATION | Device/source ingestion boundary; existing UI displays recorded observations, not fabricated sensor events. |
| Queued alert evaluation | POST /alert-rules/{identifier}/evaluate | DEFERRED_EXTERNAL_INTEGRATION | Returns task ID only; worker delivery must be configured/verified before promising evaluation. |
| Notification retry | POST /notifications/{identifier}/retry | DEFERRED_EXTERNAL_INTEGRATION | Delivery providers/workers remain external; do not promise delivery from queue acceptance. |
| Optimizer recommendation ingestion/application | POST /optimization/recommendations; POST /optimization/recommendations/{identifier}/actions | DEFERRED_EXTERNAL_INTEGRATION | Member 4 producer and governed recommendation application remain outside this UI integration. |
| Population import | POST /integrations/population | DEFERRED_EXTERNAL_INTEGRATION | Trusted dataset ingestion boundary, not an interactive operational form. |
| Offline synchronization | POST /sync/push | DEFERRED_EXTERNAL_INTEGRATION | Queue/conflict workflow remains unavailable; existing local queue is preserved. |
| Backup execution | POST /admin/backups | DEFERRED_EXTERNAL_INTEGRATION | Metadata/provider boundary; no backup/restore success is invented. |
| Public self-registration | None for this UI action | NO_BACKEND_ENDPOINT | Administrator provisioning notice; no public endpoint. |
| Individual bed reservation/patient allocation | None for this UI action | NO_BACKEND_ENDPOINT | Capacity updates do not allocate named patients or individual beds. |
| Emergency activation/simulation | None for this UI action | NO_BACKEND_ENDPOINT | No incident activation/DEFCON/convoy state contract. |
| Federated training controls | None for this UI action | DEFERRED_EXTERNAL_INTEGRATION | No working training/node-management backend contract. |
| Camera barcode capture/decoding | None for this UI action | DEFERRED_EXTERNAL_INTEGRATION | Manual registered-code lookup works; no camera integration. |
| Ambulance dispatch/crew assignment | None for this UI action | NO_BACKEND_ENDPOINT | Asset status update is not dispatch, crew scheduling or ETA calculation. |
| Unsupported settings persistence | None for this UI action | NO_BACKEND_ENDPOINT | Audio/contrast/sync interval controls disabled; browser theme remains local. |
| Prediction/risk/oxygen scenario controls | None for this UI action | NO_BACKEND_ENDPOINT | No supported prediction, outbreak-polygon or oxygen-runway mutation contract. |
| Report-job cancellation/retry | None for this UI action | NO_BACKEND_ENDPOINT | Only creation, status and download exist; pending is not running or completed. |

## Permission and state-machine constraints

- Facility/geography reads still require `inventory.read`. Facility administration is only offered through the existing readable directory; no new inventory grant is supplied. Narrow beds/workforce/aggregate writers use their assigned/permitted facility UUID instead of forbidden directory requests.
- Transfer create/action requires both source and destination scopes. Cancel/receive eligibility additionally requires an authorized successful shipment lookup (`procurement.read`); without it these controls stay hidden with an explanation. This conservative frontend dependency is not a backend permission change.
- Supplier writes require global scope. Order approval requires both procurement.write and procurement.approve. Order receipt also requires inventory.write. Real supplier/medicine/stock/parent records supply relationship options. Creation is unavailable when required directories cannot be read.
- Shipment movement uses the backend parent-state restrictions as well as its own state. Planned shipments alone can be cancelled. Shipment arrival does not itself receive stock. Tracked arrivals gate order/transfer receipt.
- Transfer safety stock is enforced at approval. Inventory issue uses backend FEFO, expiry/recall and reserved-stock checks; this contract does not impose a new dispensing safety-stock rule. No client-authoritative balances or rules were introduced.
- Report jobs require reports.read and reports.export, with workforce.read for staff and global scope for transfers. Jobs are owner-scoped. Creation accepts only facility/kind/format, not every synchronous report filter. Generator limit is 500 rows; large jobs fail with the actual failure code.
- Metadata PUT operations and maintenance events have no universal optimistic version/idempotency contract. Duplicate maintenance events and independently created report jobs remain possible across clients. Aggregate updates use expected_version; state transitions use backend row locks.

## Remaining non-GET operations without frontend coverage

**33 operations remain uncovered.** This is distinct from grouped workflow counts above. Seed/probe script calls do not count as frontend coverage.

| Operation | Disposition / workflow |
| --- | --- |
| `DELETE /report-schedules/{identifier}` | READ_ONLY_BY_DESIGN: Recurring report schedules |
| `DELETE /roles/{identifier}/permissions/{permission_id}` | READ_ONLY_BY_DESIGN: Permission grant/revocation |
| `DELETE /users/{identifier}/districts/{district_id}` | READ_ONLY_BY_DESIGN: Facility/district scope assignments |
| `DELETE /users/{identifier}/facilities/{facility_id}` | READ_ONLY_BY_DESIGN: Facility/district scope assignments |
| `DELETE /users/{identifier}/roles/{role_id}` | READ_ONLY_BY_DESIGN: User role assignment/revocation |
| `PATCH /medicines/{identifier}` | READ_ONLY_BY_DESIGN: Medicine catalogue administration |
| `PATCH /users/{identifier}` | READ_ONLY_BY_DESIGN: Account provisioning and updates |
| `POST /admin/backups` | DEFERRED_EXTERNAL_INTEGRATION: Backup execution |
| `POST /alert-rules` | READ_ONLY_BY_DESIGN: Threshold-rule administration |
| `POST /alert-rules/{identifier}/evaluate` | DEFERRED_EXTERNAL_INTEGRATION: Queued alert evaluation |
| `POST /auth/password/change` | READ_ONLY_BY_DESIGN: Password change/reset confirmation |
| `POST /auth/password/reset/confirm` | READ_ONLY_BY_DESIGN: Password change/reset confirmation |
| `POST /barcodes` | READ_ONLY_BY_DESIGN: Barcode registry administration |
| `POST /cold-chain/observations` | DEFERRED_EXTERNAL_INTEGRATION: Cold-chain ingestion |
| `POST /escalation-rules` | READ_ONLY_BY_DESIGN: Escalation-rule administration |
| `POST /integrations/population` | DEFERRED_EXTERNAL_INTEGRATION: Population import |
| `POST /medicines` | READ_ONLY_BY_DESIGN: Medicine catalogue administration |
| `POST /notifications/{identifier}/retry` | DEFERRED_EXTERNAL_INTEGRATION: Notification retry |
| `POST /optimization/recommendations` | DEFERRED_EXTERNAL_INTEGRATION: Optimizer recommendation ingestion/application |
| `POST /optimization/recommendations/{identifier}/actions` | DEFERRED_EXTERNAL_INTEGRATION: Optimizer recommendation ingestion/application |
| `POST /recalls` | READ_ONLY_BY_DESIGN: Global recall administration |
| `POST /recalls/{identifier}/resolve` | READ_ONLY_BY_DESIGN: Global recall administration |
| `POST /report-schedules` | READ_ONLY_BY_DESIGN: Recurring report schedules |
| `POST /roles` | READ_ONLY_BY_DESIGN: Role catalogue administration |
| `POST /sync/push` | DEFERRED_EXTERNAL_INTEGRATION: Offline synchronization |
| `POST /users` | READ_ONLY_BY_DESIGN: Account provisioning and updates |
| `PUT /alert-rules/{identifier}` | READ_ONLY_BY_DESIGN: Threshold-rule administration |
| `PUT /escalation-rules/{identifier}` | READ_ONLY_BY_DESIGN: Escalation-rule administration |
| `PUT /inventory/policies/{facility_id}/{medicine_id}` | READ_ONLY_BY_DESIGN: Stock-policy administration |
| `PUT /roles/{identifier}/permissions/{permission_id}` | READ_ONLY_BY_DESIGN: Permission grant/revocation |
| `PUT /users/{identifier}/districts/{district_id}` | READ_ONLY_BY_DESIGN: Facility/district scope assignments |
| `PUT /users/{identifier}/facilities/{facility_id}` | READ_ONLY_BY_DESIGN: Facility/district scope assignments |
| `PUT /users/{identifier}/roles/{role_id}` | READ_ONLY_BY_DESIGN: User role assignment/revocation |

## Complete source control audit

**169 JSX control declarations** inventoried with the TypeScript parser: buttons, forms, selects, inputs, textareas and MutationForm call sites in application source (tests excluded). Mapped controls expand into the concrete actions above; source declaration counts are not workflow counts. Shared modal, draft and confirmation controls are included. Link navigation is read-only routing; no link performs a mutation. Components with no controls still appear in the Phase 3 source inventory.

`NOT_AUTHORIZED_FOR_ROLE` is the runtime classification of any connected action whose listed grants/global scope/prerequisite access are missing, rather than an extra duplicate source row. No active operational placeholder emits fake success. The PLACEHOLDER rows below are preserved, unreachable legacy demonstrations.

| Source:line | Control / label or expression | Classification | Handling |
| --- | --- | --- | --- |
| src/components/common/BackendData.tsx:38 | button View details | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/BackendData.tsx:49 | button Refresh {title} | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/components/common/BackendData.tsx:51 | button Previous | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/BackendData.tsx:51 | button Next | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/CommandPalette.tsx:82 | input {t('actions.searchPlaceholder')} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/CommandPalette.tsx:90 | button  <X className="w-4 h-4" />  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/CommandPalette.tsx:103 | button  <div className="flex items-center gap-3"> {item.icon} <span>{item.label}</span> </div> <span className="text-xs text-slate-500 gr | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/CommandPalette.tsx:126 | button  {theme === 'dark' ? ( <> <Sun className="w-4 h-4 text-amber-400" /> <span>Switch to Light Mode</span> </> ) : ( <> <Moon classNam | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/FacilityPicker.tsx:12 | input "Facility ID" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/FacilityPicker.tsx:16 | select "Facility" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/MutationForm.tsx:43 | button Remove line {index+1} | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:43 | button Add line | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:45 | select {name} | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:45 | input {name} | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:45 | input {name} | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:60 | button {props.title} | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:94 | form <fieldset disabled={busy /  / uncertain /  / !!review}><FormFields schema={schema} values={values} change={setValues} fixed={fixed} option | CONNECTED_MUTATION | Shared validated submission/confirmation; backend confirmation and refresh. |
| src/components/common/MutationForm.tsx:96 | button {busy?'Saving...':'Confirm change'} | CONNECTED_MUTATION | Shared validated submission/confirmation; backend confirmation and refresh. |
| src/components/common/MutationForm.tsx:96 | button Back | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/MutationForm.tsx:97 | button {busy?'Saving...':props.confirm?'Review change':uncertain?'Retry same request':'Save'} | CONNECTED_MUTATION | Shared validated submission/confirmation; backend confirmation and refresh. |
| src/components/common/MutationForm.tsx:99 | button Close {uncertain?'after checking records':'completed action'} | LOCAL_ONLY | Draft fields, line controls, dialog/review state; never claims a write. |
| src/components/common/Navbar.tsx:39 | button  <Menu className="w-4 h-4" /> <span>Menu</span>  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/OfflineIndicator.tsx:60 | button "Synchronization is not implemented; queued records are preserved." | DEFERRED_EXTERNAL_INTEGRATION | Disabled sync; local queue retained. |
| src/components/common/RoleSidebar.tsx:70 | button  <X className="w-5 h-5" />  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleSidebar.tsx:156 | button "Collapse Sidebar" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleSidebar.tsx:166 | button "Expand Sidebar" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:52 | button "Open navigation drawer" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:84 | button "Command Palette" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:98 | button "Switch Language" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:111 | button  <span>English</span> <span className="text-[10px] font-mono text-slate-500">EN</span>  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:120 | button  <span>हिन्दी</span> <span className="text-[10px] font-mono text-slate-500">HI</span>  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:129 | button  <span>বাংলা</span> <span className="text-[10px] font-mono text-slate-500">BN</span>  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:143 | button "Toggle visual theme" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:163 | button  <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center font-bold text | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/RoleTopBar.tsx:211 | button  <LogOut className="w-4 h-4" /> <span>Sign Out</span>  | CONNECTED_MUTATION | Preserved Phase 1 remote logout plus session cleanup. |
| src/components/common/Sidebar.tsx:148 | button  <X className="w-5 h-5" />  | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/Sidebar.tsx:232 | button "Collapse Sidebar" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/Sidebar.tsx:242 | button "Expand Sidebar" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/common/TopBar.tsx:56 | button "Toggle Navigation Sidebar" | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:71 | button  <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200 transition-colors" /> <span className="flex-1 truncate"> | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:93 | button "Switch Simulated Role" | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:111 | button  <span>{r.label}</span> {activeRole === r.id && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:131 | button "Change Language" | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:143 | button  {l.label}  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:160 | button "Toggle Theme" | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/common/TopBar.tsx:174 | button "Notifications" | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/components/ui/EmptyState.tsx:27 | button  {actionLabel}  | READ_ONLY_BY_DESIGN | Reusable presentation callback, no independent operational endpoint. |
| src/components/ui/ErrorState.tsx:35 | button  <RefreshCw className="w-3.5 h-3.5" /> <span>Retry Connection</span>  | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/components/ui/Modal.tsx:63 | button "Close dialog" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/components/ui/Toast.tsx:60 | button "Dismiss toast" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/admin/AdminPage.tsx:12 | button {t} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/alerts/AlertsPage.tsx:17 | button {label} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/alerts/AlertsPage.tsx:18 | select "Alert status" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/alerts/AlertsPage.tsx:18 | select "Alert severity" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/alerts/AlertsPage.tsx:18 | button Refresh alerts | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/alerts/AlertsPage.tsx:19 | button {busy===a.id?'Acknowledging...':'Acknowledge'} | CONNECTED_MUTATION | Existing acknowledgement; synchronous submission guard added. |
| src/modules/alerts/AlertsPage.tsx:19 | MutationForm "Resolve alert" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/alerts/AlertsPage.tsx:19 | button Escalation history | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/AIDashboard.tsx:10 | button {label} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/AIDashboard.tsx:13 | input "Consumption medicine ID" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/AIDashboard.tsx:13 | input "Consumption start date" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/AIDashboard.tsx:13 | input "Consumption end date" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/OperationalContext.tsx:9 | input "Context district ID" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/OperationalContext.tsx:9 | input "Context medicine ID" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:27 | select "Report" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:29 | input {`Report ${label}`} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:30 | input "Report start date" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:30 | input "Report end date" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:31 | button Refresh report | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/analytics/ReportsPanel.tsx:31 | button Download page as {format.toUpperCase()} | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/analytics/ReportsPanel.tsx:33 | button Previous report page | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:33 | button Next report page | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:34 | MutationForm "Request report job" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/analytics/ReportsPanel.tsx:35 | form <input aria-label="Existing report job ID" placeholder="Existing report job ID" className={controlClass} value={jobInput} onChange | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/analytics/ReportsPanel.tsx:35 | input "Existing report job ID" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/analytics/ReportsPanel.tsx:35 | button Check report job status | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/analytics/ReportsPanel.tsx:44 | button Download completed report job | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/auth/ForgotPasswordPage.tsx:21 | form  <label htmlFor="recovery-username">Username</label> <input id="recovery-username" autoComplete="username" required value={usernam | CONNECTED_MUTATION | Preserved real login/recovery request; recovery delivery remains external. |
| src/modules/auth/ForgotPasswordPage.tsx:23 | input input | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/ForgotPasswordPage.tsx:25 | button {busy ? 'Requesting...' : 'Request recovery'} | CONNECTED_MUTATION | Preserved real login/recovery request; recovery delivery remains external. |
| src/modules/auth/LoginPage.tsx:115 | form  {/* Role Selector (Task 1 Requirement) */} <div> <label htmlFor="role-select" className="block text-xs font-bold uppercase tracki | CONNECTED_MUTATION | Preserved real login/recovery request; recovery delivery remains external. |
| src/modules/auth/LoginPage.tsx:125 | select "Role" | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:157 | input "Official Email / Username" | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:182 | button Forgot passcode / Emergency access  | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:192 | input "Passcode / Password" | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:205 | button {showPassword ? 'Hide password' : 'Show password'} | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:219 | input "text" | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:224 | input "Remember this terminal" | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:238 | button  {isLoading ? ( <> <RefreshCw className="w-4 h-4 animate-spin" /> <span>Verifying Credentials & Permissions...</span> </> ) : ( <> | CONNECTED_MUTATION | Preserved real login/recovery request; recovery delivery remains external. |
| src/modules/auth/LoginPage.tsx:274 | button ✕  | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:286 | form  <p className="text-slate-400 leading-relaxed"> Enter your official email registered with the Ministry of Health or State Health D | CONNECTED_MUTATION | Preserved real login/recovery request; recovery delivery remains external. |
| src/modules/auth/LoginPage.tsx:294 | input "officer@sanjeevani.gov.in" | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:304 | button Cancel  | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/LoginPage.tsx:311 | button Send Token Reset  | CONNECTED_MUTATION | Preserved real login/recovery request; recovery delivery remains external. |
| src/modules/auth/LoginPage.tsx:326 | button Close  | LOCAL_ONLY | Authentication input, proof, role presentation or dialog state; grants come from backend. |
| src/modules/auth/SettingsPage.tsx:41 | button  {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />} <span clas | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/auth/SettingsPage.tsx:55 | input "checkbox" | NO_BACKEND_ENDPOINT | Unsupported settings disabled; availability button explains limits. |
| src/modules/auth/SettingsPage.tsx:79 | input "checkbox" | NO_BACKEND_ENDPOINT | Unsupported settings disabled; availability button explains limits. |
| src/modules/auth/SettingsPage.tsx:93 | select  <option value="10s">10 seconds (High Precision)</option> <option value="30s">30 seconds (Balanced)</option> <option value="60s">6 | NO_BACKEND_ENDPOINT | Unsupported settings disabled; availability button explains limits. |
| src/modules/auth/SettingsPage.tsx:108 | button  <Save className="w-4 h-4" /> <span>Settings Availability</span>  | NO_BACKEND_ENDPOINT | Unsupported settings disabled; availability button explains limits. |
| src/modules/beds/BedsPage.tsx:12 | button Refresh beds | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/beds/BedsPage.tsx:14 | button View history | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/dashboard/BackendDashboard.tsx:46 | button Refresh beds chart | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/equipment/EquipmentPage.tsx:11 | button {t==='equipment'?'Biomedical Equipment':'Ambulance Fleet'} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/equipment/OperationsActions.tsx:17 | MutationForm "Update bed capacity" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:18 | MutationForm {`Register ${kind==='equipment'?'equipment':'ambulance'}`} | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:19 | MutationForm {`Edit ${kind==='equipment'?'equipment':'ambulance'}`} | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:20 | MutationForm "Record maintenance" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:21 | MutationForm "Add staff role" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:21 | MutationForm "Add staff" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:21 | MutationForm "Edit staff" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:22 | MutationForm "Create shift" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:22 | MutationForm "Cancel shift" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:23 | MutationForm "Record attendance" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/equipment/OperationsActions.tsx:24 | MutationForm {`Record ${kind==='footfall'?'footfall':'disease count'}`} | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/FacilitiesPage.tsx:20 | input "Search facilities" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilitiesPage.tsx:21 | select "Facility type" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilitiesPage.tsx:22 | select "Facility status" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilitiesPage.tsx:23 | select "State" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilitiesPage.tsx:24 | select "District" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilitiesPage.tsx:25 | select "Block" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilitiesPage.tsx:26 | button Refresh facilities | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/facilities/FacilitiesPage.tsx:36 | button View {f.name} details | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilityActions.tsx:12 | MutationForm "Create facility" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/FacilityActions.tsx:13 | MutationForm "Edit facility" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/FacilityActions.tsx:14 | select "Geography level" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/FacilityActions.tsx:14 | MutationForm "Add geography" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:37 | MutationForm "Create supplier" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:38 | MutationForm "Edit supplier" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:39 | MutationForm "Register warehouse" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:40 | MutationForm "Edit warehouse" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:41 | MutationForm "Create purchase order" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:43 | MutationForm "Create transfer" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:45 | MutationForm {`${action.replace(/_/g,' ')} ${tab==='transfers'?'transfer':'order'}`} | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:46 | MutationForm "Receive purchase order" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:47 | select "Shipment source" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/facilities/SupplyActions.tsx:47 | MutationForm "Create shipment" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/SupplyActions.tsx:48 | MutationForm {`Mark shipment ${status}`} | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/facilities/WarehouseDashboardPage.tsx:15 | button {id==='shipments'?'Shipments':d.title} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/BatchTracePanel.tsx:11 | button Previous trace page | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/BatchTracePanel.tsx:11 | button Next trace page | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/ColdChainPanel.tsx:8 | input "Cold-chain start" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/ColdChainPanel.tsx:8 | input "Cold-chain end" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/InventoryActions.tsx:8 | MutationForm "Receive stock" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/inventory/InventoryActions.tsx:9 | MutationForm "Issue stock" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/inventory/InventoryActions.tsx:10 | MutationForm "Adjust stock" | CONNECTED_MUTATION | Concrete workflow and permission/state conditions in connected table. |
| src/modules/inventory/InventoryPage.tsx:33 | input "Search inventory" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/InventoryPage.tsx:33 | button Refresh stock | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/inventory/InventoryPage.tsx:35 | button {label} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/InventoryPage.tsx:37 | select "Medicine" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/InventoryPage.tsx:40 | form <input required maxLength={128} aria-label="Barcode" className={controlClass} value={barcode} onChange={e => setBarcode(e.target.v | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/inventory/InventoryPage.tsx:40 | input "Barcode" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/inventory/InventoryPage.tsx:40 | button Look up barcode | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/map/InteractiveResourceMap.tsx:18 | button Hospitals & PHCs | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/map/InteractiveResourceMap.tsx:18 | button Warehouses & MSDs | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/map/InteractiveResourceMap.tsx:19 | button Disease Heatmap - unavailable | NO_BACKEND_ENDPOINT | Disabled unavailable layer; no fabricated operational overlay. |
| src/modules/map/InteractiveResourceMap.tsx:19 | button Emergency Heatmap - unavailable | NO_BACKEND_ENDPOINT | Disabled unavailable layer; no fabricated operational overlay. |
| src/modules/map/InteractiveResourceMap.tsx:20 | input "Search map facilities" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/map/InteractiveResourceMap.tsx:21 | select "State" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/map/InteractiveResourceMap.tsx:22 | select "District" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/map/InteractiveResourceMap.tsx:23 | select "Type" | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/modules/map/InteractiveResourceMap.tsx:24 | button Refresh map | READ_ONLY_BY_DESIGN | Read/filter/refresh/download; no domain mutation. |
| src/modules/workforce/WorkforcePage.tsx:12 | button {label} | LOCAL_ONLY | Navigation, filtering, selection, localization, theme or dismissal; no database write claimed. |
| src/pages/HomePage.tsx:83 | button  <Command className="w-4 h-4" /> <span>Launch Command Palette (Ctrl+K)</span>  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/pages/HomePage.tsx:91 | button  <span>Test Modal Dialog</span>  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/pages/HomePage.tsx:98 | button  <BellRing className="w-3.5 h-3.5 text-emerald-400" /> <span>Test Toast Notification</span>  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/pages/HomePage.tsx:245 | button Close  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/pages/HomePage.tsx:251 | button Confirm Action  | PLACEHOLDER | Unreachable legacy demonstration; no active router/import consumer. |
| src/pages/UnauthorizedPage.tsx:65 | button  <LogOut className="w-4 h-4" /> Sign Out  | CONNECTED_MUTATION | Preserved Phase 1 remote logout plus session cleanup. |

Source-control classification counts: CONNECTED_MUTATION=41, DEFERRED_EXTERNAL_INTEGRATION=1, LOCAL_ONLY=92, NO_BACKEND_ENDPOINT=6, PLACEHOLDER=13, READ_ONLY_BY_DESIGN=16.
