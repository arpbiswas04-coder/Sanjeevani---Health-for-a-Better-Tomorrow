# Supported integrated development setup

Run from the repository root. Use Python 3.11–3.13, Node 24.15.0 (the CI version), and Docker Desktop
with Compose. These commands use PowerShell; on POSIX activate
`backend/.venv/bin/activate` instead. Do not run the legacy root Compose stack
alongside this stack: it competes for ports and is not the verified PostGIS setup.

## Configuration (once per checkout)

```powershell
if (!(Test-Path backend/.venv)) { python -m venv backend/.venv }
. backend/.venv/Scripts/Activate.ps1
python -c "import sys; from pathlib import Path; assert sys.prefix != sys.base_prefix and Path(sys.prefix).resolve() == Path('backend/.venv').resolve()"
python -m pip install -r backend/requirements.txt
if (!(Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
if (!(Test-Path frontend/.env.local)) { Copy-Item frontend/.env.example frontend/.env.local }
```

Edit the local files privately. Set `POSTGRES_PASSWORD` and the matching,
URL-encoded password in `DATABASE_URL`; keep database/user `sanjeevani_dev`.
Generate a random `JWT_SECRET` of at least 32 characters using a password manager.
`JWT_REFRESH_SECRET` is reserved and unused: refresh tokens use `JWT_SECRET`.
Default API/browser ports are 8000/5173; align `VITE_BACKEND_URL`, `BACKEND_URL`,
`FRONTEND_URL`, and the JSON `BACKEND_CORS_ORIGINS` list when changing them.
Never put credentials in frontend variables. A production build requires an
explicit `VITE_BACKEND_URL` (public HTTPS API origin, or `/` for a same-origin proxy).
Production backend startup also requires explicit DATABASE_URL, REDIS_URL, FRONTEND_URL,
BACKEND_URL and BACKEND_CORS_ORIGINS; development defaults cannot silently fill them.
Vite embeds it at build time; changing deployment environment alone does not change it.

## Infrastructure, schema and administrator

```powershell
docker compose --env-file backend/.env -f backend/compose.dev.yml up -d
docker compose --env-file backend/.env -f backend/compose.dev.yml ps
Set-Location backend
python -m alembic heads
# Confirm DATABASE_URL identifies your development database before migrating.
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m app.bootstrap
python -m uvicorn app.main:app --reload --port 8000
```

Bootstrap prompts for credentials and refuses to replace an existing user. Use
your real administrator to sign in. No demo credential bypass or Phase 3/4 fixture
is required for startup. An empty database correctly renders empty operational views.
PostGIS is provided by the development image and enabled by migrations. Persistent
Compose volumes survive `stop`; never use `down -v` for ordinary shutdown.

In a second terminal, from repository root:

```powershell
Set-Location frontend
npm ci
npm run dev -- --port 5173 --strictPort
```

In separate activated backend terminals, start background processing when using
report jobs, scheduled reports, alerts and notifications:

```powershell
python -m celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo
python -m celery -A app.tasks.celery_app:celery_app beat --loglevel=info
```

Run only one Beat scheduler per environment. `solo` supports this Windows development
setup; staging needs a supervised worker/scheduler deployment. Health and OpenAPI:
`http://localhost:8000/api/v1/health`, `/api/v1/openapi.json`, `/api/v1/docs`.
Stop foreground processes with Ctrl+C. From repository root:

```powershell
docker compose --env-file backend/.env -f backend/compose.dev.yml stop
```

## Tests and isolated infrastructure verification

Frontend (from `frontend`): `npm test`, then `npm run build`.
Backend (activated `.venv`, from `backend`): `python -m pytest -q -rs`.
The default suite uses disposable SQLite and explicitly skips unconfigured external
checks. For PostgreSQL/PostGIS and Redis checks, privately create `backend/.env.local`
only if absent, setting `VERIFY_POSTGRES_PASSWORD`, `TEST_DATABASE_URL` to
`postgresql+asyncpg://verifier:<URL-encoded-password>@127.0.0.1:55432/sanjeevani_test`,
and `TEST_REDIS_URL=redis://127.0.0.1:16379/15`. The password must match Compose.
Never point test variables to the persistent development database.

```powershell
# Repository root:
docker compose --env-file backend/.env.local -p sanjeevani-verification -f backend/compose.verify.yml up -d
Set-Location backend
python -c "from dotenv import load_dotenv; load_dotenv('.env.local',override=True); import pytest; raise SystemExit(pytest.main(['-q','-rs']))"
python scripts/verify_readiness_infrastructure.py
```

The readiness script verifies an empty generated `phase5_*_test` database, migration
round trip, real HTTP authentication, queued report execution, and short-interval
Beat. It stops only its own processes and drops only its own generated database.
It requires the disposable verification role to have database/extension creation
privileges; never grant those privileges to a staging runtime account.
Logs/results go to ignored `tmp/`. TimescaleDB checks require a compatible server
and `ENABLE_TIMESCALEDB=1`; ordinary PostGIS does not supply TimescaleDB.

Phase 3/4 live React tests are opt-in and require their private account/fixture
manifests; see the phase reports and guarded scripts. They are test fixtures, not
production seeds. Preserve their ownership manifests; do not delete records by
name alone or assume old fixtures have unlimited transfer stock. A new developer
can use real UI workflows to populate development data without these manifests.

Python requirements specify supported version ranges, not an exact lock. Run the
suite when resolving a fresh environment. The frontend lockfile must remain intact.
See [FINAL_READINESS_AUDIT.md](FINAL_READINESS_AUDIT.md) for measured results and
the distinction between local verification and staging readiness.

## Development data foundation

These commands are explicit development tools, never application startup hooks.
They require `APP_ENV=development`, `postgresql+asyncpg`, a localhost/127.0.0.1
connection, and database name `sanjeevani_dev`; the connected database name is
checked before writes. Never use them in production. No migrations or new
dependencies are needed. Existing records, accounts and passwords are not reset.

### Source inspection and mappings

The root CSV files are **already tracked in Git**; this work does not add, rewrite
or remove them. The inspected row counts exclude headers:

| File | Rows | Columns |
| --- | ---: | --- |
| `India_Medicines_part_01.csv` | 283,942 | Alphabet, Page, Product Name, Image URL, Medicine Name, Price, Is Prescription Required?, Type of Medicine, Composition |
| `India_Medicines_part_02.csv` | 64,269 | Same nine medicine columns |
| `medindia_hospitals_clinics.csv` | 103,637 | name, city, pincode, state, profile_url, directory_url |

The medicine parts form one 348,211-row dataset. There are no identical full rows,
but normalized medicine names repeat 97,033 times (251,178 distinct names);
3,938 repeated-name occurrences have differing ancillary fields. Type/composition
are missing in 106,291 rows (30.53%); the scraped fields can contain concatenated
manufacturer, pack and ingredient text. Image URLs are missing in six rows and
prices in five. Use **Medicine Name**, not the concatenated Product Name, for
`Medicine.name`. Normalize Unicode/whitespace and null-like strings; derive
`MD1-<SHA256 prefix>` from the case-folded name. Set `unit=unspecified`: the source
does not reliably establish a stock unit. Do not infer dosage, composition,
manufacturer, prescription status, price or clinical facts. Unsupported fields
remain in the source CSV; source filename, line and raw-row hash go into audit
provenance. Name-based deduplication is a development catalogue policy, not a
clinically validated product identity system.

Facility source has two empty names, 317 repeated profile URLs and 3,756 repeated
normalized name/city/pincode/state tuples, with no identical full rows. There are
496 `Not Available` state/pincode placeholders. The first row is a car clinic;
the importer rejects that obvious non-healthcare pattern, but does not certify
the remaining listings as registered healthcare institutions.

Map `name` to `Facility.name`; concatenate only city, PIN and state into `address`
(not a claimed street address). Set type `other`, `source_device=dev-import:medindia:v1`,
and deterministic `FD1-<SHA256 prefix>` from normalized name/city/PIN/state.
Keep `latitude`, `longitude` and `block_id` null. URLs and source location labels
are retained in audit provenance, not repurposed as contact details. Canonical
Indian state names reuse matching India/state nodes; ambiguous existing geography
aborts. No districts, blocks or cities are fabricated. The schema links a facility
to a state through its block/district only, so imported facilities do **not** yet
participate in state/district filters. Verified hierarchy mapping is a separate
enrichment task.

### Commands and ownership

From an activated `backend/.venv`, with working directory `backend`:

```powershell
python -m scripts.development_data users --profile admin
# Prompts privately. Alternatively supply DEV_DATA_ADMIN_PASSWORD privately.
python -m scripts.development_data medicines --limit 200
python -m scripts.development_data facilities --limit 50
python -m scripts.development_data operations --seed 20261003 --facilities 3 --medicines 8
```

The first proof used 10 medicines and five facilities, then expanded to the above
limits. Two hundred names (round-robin from both medicine parts) and 50 facilities
exercise pagination and geography while keeping review manageable. This is a
bounded source-order sample, not statistically representative of India. `--limit`
counts valid distinct source identities considered, including existing records;
it is not a promise to insert that many *additional* rows.

Import commands stream CSVs, use a temporary disk-backed deduplication index and
bounded database batches (default 250, configurable `--batch-size` 1–1000).
The CLI holds a PostgreSQL advisory lock to serialize development data commands.
Same identities are skipped; conflicting owned values or profile identities are
reported, not overwritten. Matching unowned catalogue entries are left alone.
Each batch commits independently, so interrupted imports may retain completed
batches and can be rerun safely. Duplicate ancillary source variants are counted;
the first accepted identity wins. Existing source aliases are not a general
entity-resolution registry; changed source data needs conflict review.

Only request full imports deliberately, after reviewing source quality/storage:

```powershell
python -m scripts.development_data medicines --full
python -m scripts.development_data facilities --full
```

Full mode was not run against PostgreSQL in this verification. `--source-dir`
can select a directory containing the same filenames. No automatic geocoding occurs.

Synthetic operations use `DEVOPS-20261003` references, batch/staff/equipment codes,
explicit DEVELOPMENT ONLY names and SYNTHETIC bed/footfall labels. Alerts include
`development_only` and `seed` details. A separate synthetic depot is created;
source facilities are not reclassified as warehouses. Counts, expiry dates,
capacity, prices and personnel are invented development fixtures, **not real
observations about these source institutions**. The seed uses existing services
for receipts/issues, safety stock, transfer transitions, procurement, beds and
alerts. Its single transaction records an owned mutation receipt and manifest.
The same seed/configuration returns that manifest without writes; changing the
configuration for an existing seed is rejected. A different seed intentionally
creates a different dataset. Dates are relative to the first run's UTC date and
persisted in the receipt. Reproduction also depends on the selected source records.

No automated deletion is provided: stock/audit history is immutable and shared
source records may acquire references. Do not delete by prefix or reset the DB.
Use ownership audits/receipt IDs for review and supported deactivation workflows
where appropriate; any cleanup requires a separately reviewed dependency plan.

### Real development users

`users` creates only `dev-data-admin`, `dev-data-operator`, `dev-data-inventory`
or `dev-data-reader`. Passwords are prompted without echo or read from
`DEV_DATA_<PROFILE>_PASSWORD`; never put them in tracked files or command arguments.
Existing accounts/roles must match ownership, grants, password and scope, otherwise
the command refuses to alter them. It never resets `arpan` or any other password.

Use facility IDs from the operations command's returned manifest:

```powershell
python -m scripts.development_data users --profile operator --facility-id <first-facility-UUID>
python -m scripts.development_data users --profile reader --facility-id <first-facility-UUID>
python -m scripts.development_data users --profile inventory --facility-id <first-facility-UUID> --facility-id <second-facility-UUID> --facility-id <third-facility-UUID> --facility-id <depot-UUID>
```

| Account | Backend role | Actual scope/grants |
| --- | --- | --- |
| dev-data-admin | administrator | Global; existing full permission catalogue |
| dev-data-operator | dev_data_operator | First seeded source facility; operational reads, inventory/beds/workforce/equipment writes, alert management |
| dev-data-inventory | dev_data_inventory | Three source facilities plus depot; inventory read/write/transfer, procurement read/write, alerts read and report read/export |
| dev-data-reader | dev_data_reader | First seeded source facility; inventory, procurement, workforce, beds, equipment, alerts, reports/export and integration reads |

Global-only backend operations still reject restricted accounts even when they
have the route capability. Source/geography reads currently require `inventory.read`;
these profiles explicitly include it. Frontend aliases select the facility portal
only and never manufacture grants. No district/state user was invented because
the source lacks trustworthy district/block assignments. The local verification
passwords are in ignored `tmp/development-data/credentials.json`; treat that file
as private local credentials, never stage/share it. Other developers should choose
their own prompted passwords.

### Map provider and coordinate readiness

[CARTO now requires a basemap API key](https://www.carto.com/basemaps/apikey/);
the existing unauthenticated cartocdn URL caused its API-key watermark. The small
development fix changes only Leaflet's TileLayer to
`https://tile.openstreetmap.org/{z}/{x}/{y}.png`, maximum zoom 19, with visible linked
OpenStreetMap contributor attribution. No key or paid service is introduced.
Follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/):
normal interactive viewing, browser caching and Referer, visible attribution,
no bulk downloads/offline prefetch. This best-effort public service has no SLA;
review a suitable provider for deployment traffic.

The map still fetches facilities through the authenticated API and plots only
existing non-null coordinates. Of 50 imported facilities, **0 have coordinates
and 50 lack them**. Whole development DB: **58 facilities, one with coordinates,
57 without** (including the synthetic depot). The existing located fixture was
preserved. Address validation, reliable geographic matching and separately approved
geocoding/manual review are required before source facilities can become markers.

### Verification recorded 2026-10-03

Persistent target identity was checked before writes; existing DB/volumes were
not reset. Cumulative source inserts: **200 medicines, 50 facilities, one country,
13 states; zero districts/blocks**. Expanded imports inserted 190/45 after the
initial 10/5; reruns inserted zero, skipping 200/50. One invalid car-clinic row was
rejected. Operational rerun returned the original manifest and left **all application
table counts unchanged**.

| Synthetic entity | Inserted |
| --- | ---: |
| Depot facility / warehouse / supplier / staff role | 1 each |
| Medicine batches / inventory rows / ledger transactions | 9 / 33 / 59 |
| Warehouse inventory links / stock policies | 8 / 32 |
| Beds / bed history / staff / shifts / attendance / footfall / equipment | 3 each |
| Alert rules / alerts | 9 / 7 |
| Transfer / item / approval / tracking events | 1 / 1 / 1 / 5 |
| Purchase order / item / procurement history | 1 / 1 / 5 |
| Mutation receipts / sync changes | 59 / 3 |

RBAC additions: four users, three roles, 31 role-permission links, four user-role
links and six facility-scope links. Source import, accounts and seed produced 397
audit rows before HTTP verification; authentication/logout checks add their own
audit/session records. All 33 seeded inventory balances matched summed ledger
quantities, with zero outstanding reservations. These are additions, not totals
including existing Phase 3/4 fixtures.

Real HTTP on `127.0.0.1:8000`, with prefix `/api/v1`, verified all four accounts via
form `POST /auth/login`, JWT issuance and `GET /users/me`: identities, exact backend
permissions and scopes matched PostgreSQL. Restricted facility lists matched
assigned IDs. Reader bed writes returned 403, out-of-scope inventory returned 404;
logout invalidated each tested token (subsequent `/users/me` returned 401).
The saved fingerprint of `arpan`'s ID, password hash, active flag, token version,
scope and role IDs matched the original baseline; no login/reset was attempted
for that account.

Paginated API IDs were compared with database IDs, not just HTTP status:
`/facilities` (58), `/medicines` (202), `/geography/{countries,states,districts,blocks}`
(2/14/1/1), `/suppliers` (2), `/warehouses` (1), `/purchase-orders` (2), `/transfers`
(4), `/alerts` (11). These totals include preserved fixtures. Catalogue names/codes
also matched. `/inventory?facility_id=...` returned 9/8/8/8 rows for the three
source facilities/depot, with quantities and reservations matching PostgreSQL.
`/operations/{beds,staff,shifts,attendance,footfall}` and `/assets/equipment`
returned each seeded facility's database records (three per entity); bed capacity
and occupancy also matched. The frontend remains API-driven.

| Check | Result |
| --- | --- |
| New backend development-data tests | 7 passed |
| `python -m pytest -q -rs`, default environment | 89 passed, 11 external-infrastructure skips |
| Complete suite with private disposable PostgreSQL/PostGIS/Redis test configuration | **99 passed, 1 skipped**: TimescaleDB requires a compatible TimescaleDB/PostGIS test server and ENABLE_TIMESCALEDB=1 |
| `npm test`, Node 24.15.0 | **132 passed, 13 opt-in live skips**; 5 files passed, 3 skipped |
| `npm run build` | TypeScript and Vite passed; existing >500 kB chunk warning |
| Alembic | One head `c83d9e124a35`; check: no new upgrade operations |
| Map | Regression checks OSM URL/attribution and missing-coordinate handling; one real OSM PNG fetched and visually inspected without watermark |

Backend emitted the existing Starlette/httpx deprecation warning. No dependency
installation or lockfile change was made. Build used `VITE_BACKEND_URL=/` explicitly.
The map check verifies the delivered tile and React configuration; it is not a
claim of a new full-browser visual acceptance run. Existing opt-in frontend live
fixture suites were not rerun; the seeded-data verification used real HTTP above.
Private receipts/results are under ignored `tmp/development-data/`.

Remaining limitations: unverified source quality and name-based medicine identity,
unknown units, missing facility hierarchy/coordinates, no full-volume PostgreSQL
benchmark, unavailable TimescaleDB verification, and ordinary OSM availability.
No clinical use or deployment readiness is implied. The bounded development
implementation is ready for review; nothing has been committed or pushed.
