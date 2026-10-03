> Current status: see [Phase 5 readiness audit](../FINAL_READINESS_AUDIT.md) and [supported setup](../DEVELOPMENT.md). This report retains historical phase results. Phase 5 adds optional report-job idempotency (`ReportJobRequest`), real Celery worker/Beat verification, and explicit production API configuration. Earlier statements about those gaps are superseded.

# Phase 2: development environment verification

Verified 2026-10-02 on `integration/frontend-backend`.

**Phase 3 may begin against this local PostgreSQL/PostGIS/Redis environment.**
Browser-level acceptance remains unverified because the browser tool exposes no
available browsers. TimescaleDB is unavailable and its test remains skipped.
Neither limitation is represented as a successful verification or production readiness.

## Preservation and changes

Read `frontend/AUTH_INTEGRATION.md` and the existing infrastructure runbook before
continuing. All 27 pre-existing changed/untracked source files match the hashes
recorded before Phase 2, including `frontend/package-lock.json`. Phase 1 auth code
was not changed. No packages were installed, credentials printed, volumes removed,
or commits/pushes/merges/deployments performed.

Phase 2 added:

- `backend/compose.dev.yml`: separate persistent PostGIS/Redis development project.
- `backend/.env.example`: host-run backend settings template with no credentials.
- `backend/app/core/migration_filters.py`: PostgreSQL extension-ownership filter.
- `backend/tests/test_infrastructure_integration.py`: real drift, PostgreSQL auth/
  facility-permission, Redis limiter, and dependency-failure regression tests.
- This report.

Phase 2 modified `backend/alembic/env.py` to install the filter, finish the catalog
read transaction before Alembic owns the migration transaction, and recognize its
own version table in generated disposable test schemas. No migration revision,
application schema, or authentication implementation was changed.

New ignored local files were created only when absent during initial Phase 2:
`backend/.env`, `backend/.env.local`, and `frontend/.env.local`. They were reused on
resume, not regenerated or overwritten. The isolated verification account's
credentials are in ignored `tmp/phase2-auth-account.json`; they are not in this report.

## Services and database identities

Docker Desktop/engine was initially stopped and was started using the installed
Docker CLI. On resume, the existing four service containers were stopped; they
were restarted with Compose `start --wait`, without recreation.

| Service | Version / identity | Address and storage |
| --- | --- | --- |
| Docker engine / CLI | 29.8.1 | `desktop-linux` context |
| Docker Compose | v5.5.1 | Installed plugin |
| Development PostgreSQL | 16.9; database/user `sanjeevani_dev` | `127.0.0.1:5432`; `sanjeevani-development_postgres_data` |
| Development PostGIS | Extension 3.5.2 | Enabled in `sanjeevani_dev` |
| Development Redis | 7.4.11; PING passed; AOF enabled | `127.0.0.1:6379/0`; `sanjeevani-development_redis_data` |
| Verification PostgreSQL/PostGIS | Separate `sanjeevani_test`, user `verifier` | `127.0.0.1:55432`; separate verification container/storage |
| Verification Redis | 7.4.11; PING passed | `127.0.0.1:16379/15` for isolated tests |
| Backend / frontend | FastAPI / Vite development servers | `localhost:8000` / `localhost:5173` |

Both projects use `postgis/postgis:16-3.5` and `redis:7-alpine`. Image tags are local
development choices, not immutable production image pins. All four infrastructure
containers were healthy at final verification. Development database and Redis
volume mounts were inspected; no development volume is attached to verification
services. The existing root Compose file uses plain PostgreSQL and was left unchanged;
use `backend/compose.dev.yml` for this verified host-run development workflow.

Before migrating, SQL confirmed `current_database() = 'sanjeevani_dev'` and
`current_user = 'sanjeevani_dev'`. Its initially empty application schema was
migrated to the existing head. On resume, the same migrated schema survived the
container stop/start. `sanjeevani_test` was never used for normal development.

## Alembic and genuine drift

`python -m alembic heads` and `current` identify one current head:
`c83d9e124a35`. All existing revisions were applied to development. Final
`python -m alembic check` returned **No new upgrade operations detected**.

The initial drift check mistakenly proposed removing PostGIS, TIGER geocoder,
and topology extension tables. The filter now queries PostgreSQL's extension
dependency catalog and excludes only extension-owned reflected tables. It does
not hide every table absent from ORM metadata or maintain a broad table-name ignore list.

The regression test runs migrations in a generated schema of `sanjeevani_test`,
then establishes a clean drift check. It introduces an unexpected application
column, an unmanaged application table, and an application-owned table named
`spatial_ref_sys`. All three are detected as drift. Only that test-owned schema is
dropped during cleanup. The pre-existing migration-managed geography-index
exception remains; existing PostGIS tests verify that index and spatial behavior.

The new catalog query initially opened an implicit SQLAlchemy transaction that
prevented fresh migration transactions from committing. This was corrected before
the final run. Fresh-schema PostgreSQL tests now confirm migrations commit normally.

## Authentication and authorization

The confirmed development database initially contained no accounts. Bootstrap
created exactly one isolated global administrator, `phase2-verifier`, with the
standard `administrator` role and database-backed permissions. Repeating bootstrap
was explicitly rejected as a duplicate; the password hash and account count were
unchanged. No existing password was reset.

The existing frontend live tests used this account with the actual React login
component and real HTTP requests to the PostgreSQL-backed backend, without fetch
mocks. Verified:

- OAuth2 form login and backend-issued access/refresh JWTs.
- `/api/v1/users/me` returns the actual account and role.
- `/api/v1/users` accepts the real authorized access token.
- Refresh rotates the session token and protected access continues.
- Logout revokes the session; subsequent access is rejected with 401.
- Incorrect and former demo credentials are rejected.

An independent HTTP check also verified the JWT signature/issuer using the configured
signing secret, without printing it or the tokens. PostgreSQL integration tests in
disposable schemas verify restricted facility access, current-user grants, denial
of other-facility inventory and administrative access, refresh, and logout.

Final development counts: **1 user, 0 facilities, 0 inventory records**. Only the
isolated verification account and its normal auth/session/audit records were added.
Destructive schema and domain tests ran in disposable test schemas, not development.

## Redis and outage handling

Both Redis instances answered PING. Real Redis integration tests exercised atomic
auth-rate counting, rejection after the configured limit, and key expiry. Test keys
use generated names in verification Redis database 15; no FLUSH command was used.

A temporary API on `127.0.0.1:8001`, configured with production-mode auth behavior
and verification Redis, accepted a real login and logout. Stopping **only verification
Redis** caused login to return `503 AUTH_UNAVAILABLE`. Restarting that same container
restored successful login/logout. The probe was stopped afterward. Development API
login remained available, consistent with its intentionally in-process limiter.
An additional regression forces a real Redis connection error and verifies this
production-versus-development distinction.

This verifies Redis connectivity and authentication dependency behavior. Celery
worker/beat scheduling and real external notification delivery were not certified
by this phase and are not prerequisites for starting ordinary Phase 3 API integration.

## Executed tests

| Command / check | Final result |
| --- | --- |
| Full `python -m pytest -q -rs --tb=short`, with verification variables loaded | **82 passed, 1 skipped**, 105.96 seconds |
| Applicable PostgreSQL/PostGIS tests | All four existing tests executed and passed in the full suite |
| New infrastructure tests | Drift, PostgreSQL auth/facility scope, real Redis: all three passed |
| `npm test` | **61 passed, 3 skipped**; the three live tests are opt-in |
| Live frontend tests with PostgreSQL backend running | **2 passed, 1 skipped**; the stopped-backend case was not selected in this phase |
| `npm run build` | TypeScript and Vite passed; existing large-bundle warning remains |
| Alembic head/current/check | One current head; no application schema drift |
| CORS | Both configured frontend origins passed Authorization-header preflight |
| Working-tree preservation / whitespace | 27 pre-existing files unchanged byte-for-byte; `git diff --check` passed |

The single backend skip is `test_postgres_timescale_hypertable`: this server has
no available TimescaleDB extension and `ENABLE_TIMESCALEDB=0`. No compatible server
was provisioned, so no Timescale success is claimed. The suite emits the existing
Starlette/httpx deprecation warning; no dependency installation was needed.

Live frontend tests use **jsdom + real HTTP**, not an actual browser. The browser
tool returned empty application/browser inventories. Browser-enforced CORS/storage
and visual interaction remain an explicit acceptance check for a browser-capable session.

## Required teammate configuration

Backend settings read `backend/.env` when launched from `backend`; Vite reads
`frontend/.env.local`. Preserve existing files and credentials. For a new checkout,
use the examples to create private files only if absent, and generate local secrets.

| Variable | Required setting / meaning |
| --- | --- |
| `APP_ENV` | `development` for the local backend; do not use `testing` for normal use |
| `POSTGRES_DB`, `POSTGRES_USER` | `sanjeevani_dev` for this Compose project |
| `POSTGRES_PASSWORD` | Private existing local password; must match the initialized volume |
| `DATABASE_URL` | `postgresql+asyncpg://sanjeevani_dev:<URL-encoded-password>@127.0.0.1:5432/sanjeevani_dev` |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` |
| `JWT_SECRET` | Private random value of at least 32 characters; configured and retained |
| `JWT_REFRESH_SECRET` | Not required by current implementation; reserved/empty, refresh JWTs use `JWT_SECRET` |
| `FRONTEND_URL` | `http://localhost:5173` |
| `BACKEND_URL`, frontend `VITE_BACKEND_URL` | `http://localhost:8000`; verified identical |
| `BACKEND_CORS_ORIGINS` | JSON array containing `http://localhost:5173` and `http://127.0.0.1:5173` |

`backend/.env.local` holds separate verification variables: `VERIFY_POSTGRES_PASSWORD`,
`TEST_DATABASE_URL` for `sanjeevani_test`, `TEST_REDIS_URL` for port 16379/database 15,
and `ENABLE_TIMESCALEDB=0`. Normal backend startup does not load this file.
The environment files, `.venv`, and local account credential file are Git-ignored.
Do not change a Compose password while retaining a database volume unless explicitly
performing a database credential rotation; initialization variables do not reset users.

## Exact startup, test, and shutdown commands

From repository root, with Docker Desktop running, restart the already-created
containers without recreation:

```powershell
docker compose --env-file backend/.env -f backend/compose.dev.yml start --wait
docker compose --env-file backend/.env.local -p sanjeevani-verification -f backend/compose.verify.yml start --wait
```

On a new machine only, after creating its private environment files, replace
`start --wait` with `up -d --wait`. These commands use separate project storage.

Backend terminal:

```powershell
Set-Location backend # From repository root
. .\.venv\Scripts\Activate.ps1
python -c "import sys; from pathlib import Path; assert Path(sys.prefix).resolve() == Path('.venv').resolve()"
python -m alembic current
python -m alembic heads
# Apply pending revisions only after confirming DATABASE_URL identifies development:
python -m alembic upgrade head
python -m alembic check
python -m uvicorn app.main:app --reload --port 8000
```

Frontend terminal:

```powershell
Set-Location frontend # From repository root
npm run dev -- --port 5173 --strictPort
```

Full backend suite with existing disposable verification settings, from `backend`:

```powershell
.\.venv\Scripts\python.exe -c "from dotenv import load_dotenv; load_dotenv('.env.local', override=True); import pytest; raise SystemExit(pytest.main(['-q','-rs','--tb=short']))"
```

Frontend regressions, from `frontend`: `npm test` and `npm run build`.
Repeat the live PostgreSQL login checks without printing local credentials, from `backend`:

```powershell
@'
import json, os, subprocess
from pathlib import Path
a = json.loads(Path('../tmp/phase2-auth-account.json').read_text())
env = {**os.environ, 'AUTH_LIVE_TEST': '1', 'AUTH_LIVE_OUTAGE': '0',
       'AUTH_LIVE_USERNAME': a['username'], 'AUTH_LIVE_PASSWORD': a['password']}
raise SystemExit(subprocess.run(['npm.cmd', 'test', '--',
    'src/test/authLive.integration.test.tsx'], cwd='../frontend', env=env).returncode)
'@ | .\.venv\Scripts\python.exe -
```

Stop backend/frontend using Ctrl+C in their terminals. Stop infrastructure from
repository root without deleting containers or volumes:

```powershell
docker compose --env-file backend/.env.local -p sanjeevani-verification -f backend/compose.verify.yml stop
docker compose --env-file backend/.env -f backend/compose.dev.yml stop
```

At handoff, development backend/frontend and both infrastructure projects remain
running for Phase 3; only the temporary port-8001 outage probe is stopped. No Docker
volumes were deleted. No existing administrator password was changed. Browser E2E,
TimescaleDB, and production operational certification remain outside verified results.
