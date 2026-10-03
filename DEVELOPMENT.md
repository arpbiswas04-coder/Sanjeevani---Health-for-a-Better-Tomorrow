# Supported integrated development setup

Run from the repository root. Use Python 3.11–3.13, Node 20+, and Docker Desktop
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
