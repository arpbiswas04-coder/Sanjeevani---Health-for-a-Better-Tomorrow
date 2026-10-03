# Development account coverage

Verified 2026-10-04 against local `sanjeevani_dev`. Account changes are isolated on
`feature/development-portal-accounts`; UI redesign work remains on its separate branch.

## Before and after

Before this task there were four DB roles: `administrator`, `dev_data_operator`,
`dev_data_inventory`, `dev_data_reader`. Only system/facility presentation categories
had live identities. National/state/district/facility-admin names were frontend
compatibility aliases without provisioned policies. Supplier and staff-role records
are not separately authenticated portals; no supplier/officer accounts were invented.

The guarded development command now explicitly provisions four reviewed capability
policies: `national_admin`, `state_admin`, `district_admin`, `facility_admin`.
There are eight DB roles and eight manual-test accounts. Existing accounts remain;
`dev-data-admin` is reused for SUPER_ADMIN instead of duplicating it.
`arpan` and the legacy `phase2-verifier` are not manual-test additions and are untouched.

## Complete manual-login matrix

Passwords are deliberately absent here. Use the retrieval command below.

| Portal / category | Username | Backend role | Scope / assignment | Landing page |
|---|---|---|---|---|
| SUPER_ADMIN | dev-data-admin | administrator | Global platform; 26 capabilities | `/admin/dashboard` |
| NATIONAL_ADMIN | dev-national-admin | national_admin | Global operational; 17 capabilities, no platform administration | `/national/dashboard` |
| STATE_ADMIN | dev-state-admin | state_admin | Restricted; snapshot of all existing districts in DEV3S; 16 capabilities | `/state/dashboard` |
| DISTRICT_ADMIN | dev-district-admin | district_admin | Restricted; DEV3D only; 14 capabilities | `/district/dashboard` |
| FACILITY_ADMIN | dev-facility-admin | facility_admin | Restricted; DEV-PHASE3 hospital only; 14 capabilities | `/facility/dashboard` |
| Facility operator | dev-data-operator | dev_data_operator | Restricted; A Beautiful Mind Clinic only; 14 capabilities | `/facility/dashboard` |
| Warehouse/inventory | dev-data-inventory | dev_data_inventory | Restricted; A Beautiful Mind Clinic, A C Hospital, A I I M S Hospital, DEVOPS-20261003-DEPOT; 8 capabilities | `/facility/dashboard` |
| Read-only facility | dev-data-reader | dev_data_reader | Restricted; A Beautiful Mind Clinic only; 9 capabilities | `/facility/dashboard` |

## Truthful geography and scope semantics

Existing hierarchy reused unchanged:

- Country: DEVELOPMENT ONLY Phase 3 countries (`DEV3C`).
- State: DEVELOPMENT ONLY Phase 3 states (`DEV3S`), `79011528-6982-4209-9b12-43c1940df5c3`.
- District: DEVELOPMENT ONLY Phase 3 districts (`DEV3D`), `114c8723-9f3c-45f3-bd24-4b7198ebbf27`.
- Block: DEVELOPMENT ONLY Phase 3 blocks (`DEV3B`), `8ce3ceda-2bd8-4bd1-9e5f-54d06558061b`.
- Facility: DEVELOPMENT ONLY Phase 3 Hospital (`DEV-PHASE3`), `617d9388-e638-47d8-81c6-ab953aee427e`.

No source facility was reassigned; no geography or coordinates were fabricated.
The database currently has only one linked district and one linked hospital in this
synthetic hierarchy. State, district and facility accounts therefore currently see
that same hospital, through different grant mechanisms. This is not evidence of
three different geographical datasets. Isolated PostgreSQL tests establish the
policy differences with two states, three districts and four facilities: state sees
three, district sees two, facility sees one, national sees all four test facilities.
Those isolated fixtures are never inserted into the persistent development database.

There is no native user-state or user-country scope model. State policy uses existing
`UserDistrict` grants for every district currently belonging to the selected state.
New districts are NOT automatically granted; rerunning after a district-set change
fails safely instead of silently expanding scope. A production dynamic state policy
would need a separate reviewed design. National policy uses supported global scope
with operational permissions, not an India-only country boundary. Imported hospitals
without verified block/district linkage remain excluded from regional accounts.

## Capabilities, navigation and denials

Base operational policy (14): inventory.read/write, procurement.read,
workforce.read/write, beds.read/write, equipment.read/write, alerts.read/manage,
reports.read/export and integration.read.

- Facility and district: base operational policy within their scope.
- State: base plus inventory.transfer and procurement.write.
- National: state policy plus procurement.approve, global operational scope.
- System: existing full catalogue including admin.users/admin.config/audit.read.
- Existing inventory account retains its narrower inventory/procurement/report grants;
  existing reader retains only read/export capabilities. No grants were changed.

New policies do not grant admin.users, admin.config, audit.read, facility.manage,
inventory.recall, integration.write, sync.write, emergency.activate or federation.manage.
Roles never bypass FastAPI permission checks, `facility_filter`, `check_facility`,
global-only restrictions or business/state rules. No authentication implementation,
password hashing, application scope enforcement or migration was changed.

National, state and district sidebars now have real mapped identities. Existing
capability filtering still hides unsupported emergency/federation/admin operations.
Each account's visible links and destinations were checked against its real profile;
regional landing pages remain their existing implementations, not redesigned pages.
Shared reference catalogues/geography are not all jurisdiction-filtered. These are
reference reads, not a claim of row-level isolation for every API in the product.

Login offers all five presentation categories plus automatic detection. Selecting
one never grants permissions. The selected category must match the authenticated
backend role; all eight accounts were tested with a matching choice and a conflicting
choice. Conflicts leave no authenticated frontend state or retained local token.

## Provisioning and local credentials

With `backend/.venv` active, from `backend`:

```powershell
python -m scripts.development_data portals --state-id 79011528-6982-4209-9b12-43c1940df5c3 --district-id 114c8723-9f3c-45f3-bd24-4b7198ebbf27 --facility-id 617d9388-e638-47d8-81c6-ab953aee427e
```

The command verifies development mode, localhost and exact database `sanjeevani_dev`,
uses the existing advisory lock, validates the existing hierarchy, checks exact role
permissions/account ownership/scope, and hashes passwords normally. It rejects
conflicts rather than changing existing grants or resetting passwords. Replay created
zero accounts. Four new users and four roles were created on the initial run.

New random passwords live in ignored `tmp/development-data/portal-credentials.json`.
Existing passwords remain in ignored `tmp/development-data/credentials.json`.
`SANJEEVANI_DEV_TEST_PASSWORD` may supply the initial new-account passwords only when
creating a new credential file; existing files/passwords are never overwritten.
The credential file must resolve beneath ignored workspace `tmp/`.

From repository root, this exact LOCAL PowerShell command displays all eight logins:

```powershell
$files = @('.\tmp\development-data\credentials.json', '.\tmp\development-data\portal-credentials.json')
foreach ($file in $files) {
    $records = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
    $records.PSObject.Properties.Value | Select-Object username, password
}
```

Do not copy the output into tracked files. No actual passwords are in this document.

## Verification results

- Affected backend authorization/development suite: **29 passed**, no skips:
  test_development_portals, test_development_accounts, test_development_data,
  test_security, test_identity, test_report_jobs_scopes, test_frontend_auth_contract.
- New portal tests exercise normal JWT auth against both SQLite and migrated disposable
  PostgreSQL/PostGIS schemas via FastAPI ASGI transport. Cross-state, cross-district
  and cross-facility reads and writes are allowed/denied at the backend; rejected bed
  writes leave no database row. Idempotency, wrong hierarchy and password conflict
  refusal are covered. This is API/PostgreSQL verification, not a browser test.
- Real network HTTP: **8 accounts passed**, `/api/v1/auth/login` -> JWT ->
  `/api/v1/users/me` roles/permissions/scope matched independent SQL, facility directory
  matched SQL scope, permitted inventory reads, denied admin reads/writes, outside-scope
  inventory/bed denial, `/api/v1/auth/logout` -> old-token reads/writes 401.
- Four new portal accounts each performed an allowed bed PUT, verified in SQL and a
  subsequent GET. The four labeled `DEV-PORTAL-*` bed categories (capacity 2, occupied 1)
  belong only to the existing synthetic hospital. They are verification fixtures, not
  clinical observations. Existing bed categories were not overwritten. Existing account
  mutation capabilities were not newly expanded; the read-only profile remains read-only.
- `arpan`: provisioner and HTTP verifier compare all identity columns including hash,
  roles, effective permissions, facility and district assignments; unchanged.
- Rendered React + real HTTP: **8 passed**, matching dropdown choice, JWT profile,
  landing, complete permitted navigation, guarded real facility rendering, restricted
  admin-route denial, logout invalidation and mismatched portal rejection.
- Normal frontend suite: **138 passed, 25 opt-in skips**, including the eight live tests
  that were separately enabled and passed. No skipped test counted as passed.
- TypeScript (`tsc`) and production build: **passed**. Existing >500 kB chunk warning.
- Actual browser automation: **NOT RUN**; rendered React checks are not browser acceptance.
- Full backend suite: **NOT RUN for this task**; relevant authorization tests above ran.

Real HTTP command: `python -m scripts.verify_development_portals` from backend.
It targets localhost:8001 and validates the development DB before any fixture writes.
Live frontend command (Node 24, frontend directory):

```powershell
$env:VITE_BACKEND_URL='http://127.0.0.1:8001'
$env:PORTAL_ACCOUNTS_LIVE='1'
npm test -- src/test/portalAccountsLive.integration.test.tsx
Remove-Item Env:PORTAL_ACCOUNTS_LIVE
```

All five portals can now be tested as development identities. Real regional operational
coverage, dynamic future-district membership and country-boundary isolation remain
limitations, not verified production features. No unsupported frontend metric was added.

## Isolated branch verification

After separating from the UI redesign, the dedicated account worktree passed
29 affected backend tests, 138 normal frontend tests (25 opt-in skips), and all
eight explicitly enabled real-account React/HTTP checks. TypeScript and production
build passed with the existing chunk-size warning. Real HTTP verification confirmed
eight accounts and unchanged arpan identity. The running local FastAPI application
code is identical to this branch; only development scripts and frontend functional
role choices differ. No UI redesign styling is included.

The first isolated live run hit the unchanged 20-logins/60-second development rate
limit after the separate HTTP checks (6 passed, 2 rate-limited). After the window
expired, all 8 passed without changing the limiter or test assertions.
