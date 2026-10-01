# Infrastructure verification (not executed here)

Docker is not installed in the current execution environment. Local ports 5432
and 6379 were not reachable. No production database, broker, worker, beat,
external notification, HL7, or backup/restore execution has been certified.

The root docker-compose.yml uses plain postgres:16-alpine, which does not supply
PostGIS. Use the separate disposable verification project below; it does not
mount the application data volume. The verification Compose files have been
reviewed but cannot be Docker-validated in this environment.

## PostgreSQL, PostGIS, and Redis

Run in PowerShell from the repository root with Docker Desktop running:

```powershell
$ErrorActionPreference = 'Stop'
. .\backend\.venv\Scripts\Activate.ps1
python -c "import sys; from pathlib import Path; assert Path(sys.prefix).resolve() == Path('backend/.venv').resolve()"
$env:VERIFY_POSTGRES_PASSWORD = [Guid]::NewGuid().ToString('N')
docker compose -p sanjeevani-verification -f backend/compose.verify.yml up -d --wait postgres redis
if ($LASTEXITCODE -ne 0) { throw 'Verification services did not start' }
docker compose -p sanjeevani-verification -f backend/compose.verify.yml exec -T postgres psql -U verifier -d sanjeevani_test -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"
docker compose -p sanjeevani-verification -f backend/compose.verify.yml exec -T redis redis-cli ping
$env:TEST_DATABASE_URL = 'postgresql+asyncpg://verifier:' + $env:VERIFY_POSTGRES_PASSWORD + '@127.0.0.1:55432/sanjeevani_test'
$env:DATABASE_URL = $env:TEST_DATABASE_URL
$env:REDIS_URL = 'redis://127.0.0.1:16379/0'
$env:ENABLE_TIMESCALEDB = '0'
Set-Location backend
python -m pytest -q -rs tests/test_postgres.py
python -m alembic upgrade head
python -m alembic heads
python -m alembic check
```

Expected: PostgreSQL writer, PostGIS, immutability and sync-commit-order tests
execute. The Timescale-specific test remains skipped in this configuration.
Stop on any failed command. These commands apply migrations only to the newly
created disposable `_test` database, not an application database.

## TimescaleDB extension and actual hypertable

Use a fresh verification project before its first migration. Do not silently
replace a running PostgreSQL container image attached to existing data. Stop the
previous verification project first if it occupies port 55432. Retain the same
password environment variable while its data exists.

From the repository root, with the verification password environment variable set:

```powershell
docker compose -p sanjeevani-verification -f backend/compose.verify.yml stop
docker compose -p sanjeevani-timescale-verification -f backend/compose.verify.yml -f backend/compose.timescale.verify.yml up -d --wait postgres redis
if ($LASTEXITCODE -ne 0) { throw 'Timescale verification services did not start' }
docker compose -p sanjeevani-timescale-verification -f backend/compose.verify.yml -f backend/compose.timescale.verify.yml exec -T postgres psql -U verifier -d sanjeevani_test -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS timescaledb;"
$env:ENABLE_TIMESCALEDB = '1'
$env:TEST_DATABASE_URL = 'postgresql+asyncpg://verifier:' + $env:VERIFY_POSTGRES_PASSWORD + '@127.0.0.1:55432/sanjeevani_test'
$env:DATABASE_URL = $env:TEST_DATABASE_URL
$env:REDIS_URL = 'redis://127.0.0.1:16379/0'
Set-Location backend
python -m pytest -q -rs tests/test_postgres.py
python -m alembic upgrade head
python -m alembic check
```

All five PostgreSQL tests should execute here. A skip is not a successful
Timescale verification. The HA image contains PostgreSQL, PostGIS and TimescaleDB;
choose a reviewed immutable image digest for production rather than these test tags.

## Celery worker, broker, and beat

Keep the same DATABASE_URL and REDIS_URL in each terminal, with the venv activated
and cwd `backend`. First apply migrations to the disposable public schema as above.
Start a worker in one terminal:

```powershell
python -m celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo
```

In another terminal using the same environment, exercise an actual broker task
and wait for its result:

```powershell
python -m celery -A app.tasks.celery_app:celery_app inspect ping
python -c "from app.tasks.celery_app import celery_app; r=celery_app.send_task('reports.generate'); print(r.get(timeout=30))"
```

An empty queue returns zero; timeout or worker failure is a failed check. This
proves task transport/execution, not every domain workflow. Then start exactly one
beat process, writing its runtime schedule to the OS temporary directory:

```powershell
python -m celery -A app.tasks.celery_app:celery_app beat --loglevel=info --schedule "$env:TEMP/sanjeevani-verification-celerybeat"
```

Observe beat enqueue `reports.generate` and the worker receive and successfully
complete the periodically dispatched task. Merely starting beat or getting PONG
from Redis does not verify scheduled execution. Stop worker/beat with Ctrl+C.
Production pool/process supervision remains Member 4's responsibility.

Real email/SMS/push adapters, HL7 exchange, and encrypted backup/restore drills
require their own configured providers and data. See BACKUP_RUNBOOK.md. None is
replaced by the local adapter mocks.

## Timescale design

Migration b72c8d013f24 creates `cold_chain_samples` with a composite
UUID/time primary key and a facility/time index. `ENABLE_TIMESCALEDB=1` opts into
extension creation and a seven-day hypertable on PostgreSQL; SQLite never loads
an extension. Source observations retain global source/event uniqueness and all
relational foreign keys. Their immutable sample projection is written in the
same transaction and is used by `GET /api/v1/cold-chain/series`.

The projection intentionally has no independent foreign keys: source observation
records remain authoritative and enforce relationships, while the projection is
rebuildable and compatible with Timescale constraint restrictions. No retention
policy deletes operational data. Bed occupancy history remains ordinary indexed
SQL storage: no evidence currently justifies duplicating its lower-volume data.
This implements the Timescale requirement for sensor telemetry, rather than
silently waiving it.

Pause ingestion while deploying/backfilling the migration; its PostgreSQL source
lock has a ten-second acquisition timeout. Budget time/storage for the existing
observation count. The hypertable is created empty before backfill. Downgrade drops
only the rebuildable projection. Enabling the flag after this revision has already
run does not convert an existing deployment: introduce a separately reviewed
Alembic conversion migration instead of manual production DDL or downgrading data.

References: [Timescale hypertable API](https://raw.githubusercontent.com/timescale/docs/latest/api/hypertable/create_hypertable.md),
[official Timescale HA image](https://github.com/timescale/timescaledb-docker-ha),
[official PostGIS image](https://github.com/postgis/docker-postgis).
