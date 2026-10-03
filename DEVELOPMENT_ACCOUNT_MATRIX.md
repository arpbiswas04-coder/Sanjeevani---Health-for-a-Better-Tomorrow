# Development manual-login matrix

Verified 2026-10-03 on `feature/functional-completion`, local `sanjeevani_dev`.
This is a development testing reference, not a production role policy.

## Authoritative role discovery

The database contains **four roles**, all covered by existing development accounts.
The backend is capability-based: `roles`, `role_permissions`, `user_roles`,
`user_facilities`, and `user_districts` govern access. A role name alone grants nothing.
`app/bootstrap.py` provisions `administrator` with the 26-capability catalogue.
`scripts/development_seed.py:PROFILES` defines the three narrower development profiles.
Migrations do not provision national/state/district officer policies. Staff roles
describe personnel records; they are not authenticated user roles.

Reviewed backend bootstrap, permission catalogue, identity/scope enforcement,
role migrations, actual PostgreSQL rows, frontend `authService.BACKEND_ROLES`,
`roleRoutes`, `navigationConfig`, `authorization`, `RoleGuard`, and `router.tsx`.

| Category | Username | Backend role | Scope | Password source | Landing page |
|---|---|---|---|---|---|
| System administrator | dev-data-admin | administrator | global; no artificial regional assignment | Private local credentials JSON: `admin.password` | `/admin/dashboard` |
| Facility operations | dev-data-operator | dev_data_operator | restricted; A Beautiful Mind Clinic only | Private local credentials JSON: `operator.password` | `/facility/dashboard` |
| Warehouse / inventory | dev-data-inventory | dev_data_inventory | restricted; three imported facilities plus synthetic depot | Private local credentials JSON: `inventory.password` | `/facility/dashboard` |
| Read-only facility | dev-data-reader | dev_data_reader | restricted; A Beautiful Mind Clinic only | Private local credentials JSON: `reader.password` | `/facility/dashboard` |

The private file is `tmp/development-data/credentials.json`, ignored by Git.
All four accounts remain unchanged, including their current passwords. **Zero new
accounts** were needed; the new command reused four and reported no uncovered DB roles.
`arpan` and the older `phase2-verifier` are also administrator identities, not extra
role categories. Neither was repurposed, password-reset, or used for these logins.

System admin maps to `SUPER_ADMIN`; all three scoped profiles map to `FACILITY_ADMIN`
for presentation only. The latter alias does not grant administrator capabilities.

## Assignments and limits

| Facility | ID | Assigned accounts |
|---|---|---|
| A Beautiful Mind Clinic | `563bc877-ebcd-459e-b7de-791a0a28461f` | operator, inventory, reader |
| A C Hospital | `6771d810-2009-4204-9997-5e279baae83d` | inventory |
| A I I M S Hospital | `c5a2b501-e7ec-4b5d-83cc-a2b4c73a6525` | inventory |
| DEVELOPMENT ONLY synthetic supply depot 20261003 | `a75516b1-9462-494b-92f0-2ec6c709e7a6` | inventory |

These records have no trusted block/district assignment. No hierarchy was invented.
The backend supports global/restricted scope with explicit facilities or districts;
there is no native user-state assignment model. A future state policy needs reviewed
jurisdiction relationships and permissions, not a global account renamed “state”.

| Frontend mapping without a provisioned profile | Presentation / possible landing | Disposition |
|---|---|---|
| `admin`, `super_admin` | SUPER_ADMIN / `/admin/dashboard` | Compatibility aliases only; actual production bootstrap name is `administrator` |
| `national_admin`, `national_officer` | NATIONAL_ADMIN / `/national/dashboard` | No DB role or defined capability policy; no fabricated account |
| `state_admin`, `state_officer` | STATE_ADMIN / `/state/dashboard` | No DB role/policy or native state scope; no fabricated account |
| `district_admin`, `district_officer` | DISTRICT_ADMIN / `/district/dashboard` | No DB role/policy; imported test facilities lack trustworthy district hierarchy |
| `facility_admin` | FACILITY_ADMIN / `/facility/dashboard` | Unprovisioned compatibility alias; use the actual scoped development profiles |

Existing system-admin route guards also permit national/state/district/facility
pages. The admin account can manually inspect these presentations by URL; this is
global administrator access, **not verification of regional identity or scope**.
The login selector now offers assigned-role auto-detection, System Administrator,
and Facility / inventory / read-only portal. It explains the unprovisioned regional
profiles. Compatibility mappings/routes remain intact for future governed roles.
The selector is not submitted as a backend permission grant; mismatches are rejected
against `/users/me`, with no authenticated frontend state or retained local tokens.

## Expected navigation and actions

| Role | Navigation sections | Allowed | Must not imply / allow |
|---|---|---|---|
| administrator | Operational Data, System Management, Jurisdictions, Infrastructure | All 26 backend capabilities; global reference/operational reads, admin user/config/audit access; regional pages through existing guards | No business-rule bypass; no session after logout; unsupported AI/emergency implementations remain unavailable despite capability names |
| dev_data_operator | Shared Operational Tools, Facility Operations, Clinical Care & Assets, Alerts & Profile | Selected facility inventory receive/issue, beds/workforce/equipment writes, alert management; reports/export and operational reads | Admin/config, procurement write/approve, transfers, recalls, outside-facility reads |
| dev_data_inventory | Shared Operational Tools; Facility Operations without beds; Alerts & Profile; no Clinical Care & Assets | Four-facility inventory and transfers; procurement create/write; reports/export and alerts read | Admin/config, procurement approval, bed/workforce/equipment APIs, alert management, outside-scope facilities |
| dev_data_reader | Shared Operational Tools, Facility Operations, Clinical Care & Assets, Alerts & Profile | Scoped operational/reference reads and reports/export | Operational writes, alert management, admin/config and outside-facility reads |

Mutation authorization above is the capability contract, not a claim that every
possible mutation was executed in this account-only task. Existing state machines,
FEFO, safety stock, facility scope, audit behavior and password hashing are unchanged.
Catalogue/geography access still uses `inventory.read`; no permission was added to
work around that existing contract. Reference endpoints are not all jurisdictional.

## Safe provisioning and passwords

From `backend`, with `backend/.venv` active:

```powershell
python -m scripts.development_data accounts --seed 20261003 --credentials-file ../tmp/development-data/credentials.json
```

This uses the existing localhost / development / exact-database guard, advisory lock,
owned operational seed receipt, and account provisioning helper. It verifies exact
role grants, active owned facilities and existing account ownership. Unexpected role,
scope, district assignment or password fails; the transaction rolls back. It never
resets a password, modifies `arpan`, imports datasets or invents role policies.

For a fresh compatible seeded environment, set `SANJEEVANI_DEV_TEST_PASSWORD` privately
and omit `--credentials-file`. The shared value is hashed through the normal existing
hasher. It takes precedence over a supplied file and must match any existing account;
it is not a password-reset facility. No shared value is currently configured in this
session; the existing per-account private credentials are preserved. Do not put actual
passwords in tracked documentation or source code. The public command output provides
username, category, role, exact permissions, assignment IDs, portal, landing and source.

## Verification

- Backend affected suite: **14 passed** (`test_development_accounts.py`,
  `test_development_data.py`, `test_frontend_auth_contract.py`); includes three new
  matrix tests, account creation/replay, password-source precedence, conflict refusal,
  protected administrator identity, scope, login and logout. No backend test skips.
- Frontend targeted auth/functional tests: **48 passed**.
- Complete normal frontend suite: **138 passed, 17 opt-in skips**.
- Live rendered React + real HTTP: **4 passed**, one per account. Login form, actual
  JWT/profile, landing, sidebar, guarded inventory and populated pages, forbidden
  admin route for restricted users, regional allowance for system admin, mismatched
  portal error, logout and old-token rejection verified. No HTTP mocks. Leaflet's DOM
  renderer is mocked; this is not a browser visual test.
- Real PostgreSQL-backed HTTP: all four `/api/v1/auth/login` -> `/api/v1/users/me`
  profiles match exact roles, permissions and explicit assignments; inventory records
  match SQL. `/api/v1/users` returns 200 for admin and 403 for all restricted accounts;
  out-of-scope inventory returns 404 for each restricted account; inventory-role staff
  reads and reader bed writes return 403. Logout -> old-token `/users/me` returns 401
  for every account. A full-capability administrator has no artificial capability
  denial; its denied check is the revoked session, not a fabricated restricted role.
- `arpan`: all user columns (including password hash), roles, effective permissions,
  facilities and districts unchanged; original pre-foundation signature also matches.
- TypeScript and production build: **PASSED**; existing >500 kB chunk warning.
- Browser automation: **UNAVAILABLE**, not claimed as passed.
- Full backend/infrastructure suite not repeated for this development-script/login-UI
  addition; preceding phase result remains **102 passed, 1 TimescaleDB skip**. It does
  not include the three new matrix tests, which ran in the affected suite above.

No commit, push, merge or deployment. Existing functional-completion work is preserved.

## Exact verified backend permission sets

**administrator** (26): `admin.config`, `admin.users`, `alerts.manage`, `alerts.read`, `audit.read`, `beds.read`, `beds.write`, `emergency.activate`, `equipment.read`, `equipment.write`, `facility.manage`, `federation.manage`, `integration.read`, `integration.write`, `inventory.read`, `inventory.recall`, `inventory.transfer`, `inventory.write`, `procurement.approve`, `procurement.read`, `procurement.write`, `reports.export`, `reports.read`, `sync.write`, `workforce.read`, `workforce.write`.

**dev_data_inventory** (8): `alerts.read`, `inventory.read`, `inventory.transfer`, `inventory.write`, `procurement.read`, `procurement.write`, `reports.export`, `reports.read`.

**dev_data_operator** (14): `alerts.manage`, `alerts.read`, `beds.read`, `beds.write`, `equipment.read`, `equipment.write`, `integration.read`, `inventory.read`, `inventory.write`, `procurement.read`, `reports.export`, `reports.read`, `workforce.read`, `workforce.write`.

**dev_data_reader** (9): `alerts.read`, `beds.read`, `equipment.read`, `integration.read`, `inventory.read`, `procurement.read`, `reports.export`, `reports.read`, `workforce.read`.


## Final working tree

`git diff --check`: passed. No private credential value matches in changed/new files;
no lockfile, migration or source CSV changes. The prior functional-completion changes
are preserved. This task changes/adds DEVELOPMENT.md, this document, the prior audit
checkpoint note, development_data.py, development_accounts.py, the HTTP verifier,
test_development_accounts.py, LoginPage.tsx, authRoleRouting.test.tsx and
functionalLive.integration.test.tsx.

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
 M frontend/src/modules/auth/LoginPage.tsx
 M frontend/src/modules/equipment/EquipmentPage.tsx
 M frontend/src/modules/facilities/FacilitiesPage.tsx
 M frontend/src/modules/inventory/InventoryPage.tsx
 M frontend/src/modules/map/InteractiveResourceMap.tsx
 M frontend/src/modules/workforce/WorkforcePage.tsx
 M frontend/src/services/backendTypes.ts
 M frontend/src/test/authRoleRouting.test.tsx
?? DEVELOPMENT_ACCOUNT_MATRIX.md
?? FUNCTIONAL_COMPLETION_AUDIT.md
?? backend/app/services/location_context.py
?? backend/scripts/data/development_city_references.json
?? backend/scripts/development_accounts.py
?? backend/scripts/development_enrichment.py
?? backend/scripts/verify_functional_completion.py
?? backend/tests/test_development_accounts.py
?? backend/tests/test_development_enrichment.py
?? frontend/src/test/functionalCompletion.test.tsx
?? frontend/src/test/functionalLive.integration.test.tsx
```
