# Backend foundation

This is the first implemented slice of the Member 2 blueprint, not the complete platform.

Implemented: async SQLAlchemy persistence, initial Alembic migration, Argon2 password
hashing, 15-minute JWT access tokens, database-backed role permissions, administrator
bootstrap, facility and medicine creation/listing, stock receipt, FEFO stock issue,
batch stock listing, stock transaction ledger and mutation audit records.

## Local setup (Windows)

Run from the repository root. Never install Python dependencies globally.
If the environment is missing, create it with `python -m venv backend/.venv`.
Use a Command Prompt terminal for activation if PowerShell blocks Activate.ps1:

```bat
call backend\.venv\Scripts\activate.bat
python -c "import sys; from pathlib import Path; assert sys.prefix != sys.base_prefix; assert Path(sys.prefix).resolve() == Path('backend/.venv').resolve(); print(sys.executable)"
python -m pip install -r backend\requirements.txt
cd backend
```

Create a local `backend/.env` (already ignored by Git) with:

```dotenv
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/sanjeevani
JWT_SECRET=REPLACE_WITH_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS
```

Generate a secret locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Use your own PostgreSQL credentials and provision the database before migrating.
Run commands from `backend` so the settings loader reads `backend/.env`:

```bat
python -m alembic upgrade head
python -m app.bootstrap
python -m uvicorn app.main:app --reload
```

Bootstrap prompts for a username/password; there are no default accounts. It creates
an administrator with `facility.manage`, `inventory.read` and `inventory.write`.
Permissions currently apply across all facilities; geographic/facility scoping is
not implemented yet.

Open http://localhost:8000/api/v1/docs and use Authorize to sign in. The login
endpoint takes OAuth2 form fields `username` and `password`. Its response follows
OAuth2 (`access_token`, `token_type`, `expires_in`) for Swagger interoperability.
Other new endpoints use `{ "success": true, "data": ... }`; handled errors use
`{ "success": false, "error": { "code": ..., "message": ... } }`.
Existing root and health contracts remain compatible with the scaffold.

## API sequence

1. `POST /api/v1/facilities`: `{"name":"Example PHC","code":"PHC-001"}`.
2. `POST /api/v1/medicines`: `{"name":"Example medicine","code":"MED-001","unit":"tablet"}`.
3. `POST /api/v1/inventory/receive` with the returned IDs:

```json
{
  "facility_id": "<facility UUID>",
  "medicine_id": "<medicine UUID>",
  "batch_number": "BATCH-001",
  "expires_on": "2030-12-31",
  "quantity": 100,
  "reference": "delivery-001"
}
```

4. `POST /api/v1/inventory/issue` with `facility_id`, `medicine_id`, positive
   integer `quantity` and `reference`. The response contains batch allocations.
5. `GET /api/v1/inventory?facility_id=<UUID>` and
   `GET /api/v1/inventory/transactions?facility_id=<UUID>` inspect balances/ledger.

List endpoints accept `offset` and `limit` (maximum 200). FEFO excludes recalled
batches and batches expiring today or earlier, using the UTC date. Batch numbers
are unique per medicine; receiving the same batch with a different expiry fails.
Receipts and issues update the balance, ledger and audit log in one transaction.
PostgreSQL writers lock facility then medicine before batch/balance updates, including
when the stock row does not exist. This coarse locking favors correctness over
throughput. All future stock writers must follow that locking order.
There are no API operations to edit/delete ledger entries or hard-delete records.
Direct database writes are outside these application guarantees.
`reference` is descriptive, not an idempotency key: retrying a successful write
creates another transaction. Retry protection is still to be implemented.

## Verification

```bat
python -m pytest -q
python -m alembic heads
python -m alembic check
```

Tests use isolated temporary SQLite databases with foreign keys enabled, without
requiring PostgreSQL or modifying the configured application database. They cover
login, permissions, invalid tokens, FEFO, ledger/balance consistency, rollback on
insufficient stock, recalled/expired stock, validation, duplicate records and OpenAPI.
SQLite tests cannot verify PostgreSQL row-lock behavior; live PostgreSQL migration
and concurrent-writer tests are required before deployment.

## Remaining blueprint work

- Refresh token rotation/revocation, logout, password reset, MFA, login rate limits,
  user administration and scoped permissions.
- Stock adjustment, idempotent writes, transfers and approval workflow, DOS,
  safety stock, reorder suggestions, recall management and alert rules/tasks.
- Warehouses, suppliers, procurement, shipments and cold-chain monitoring.
- Beds, workforce, attendance, footfall, equipment and ambulances.
- Notifications, escalation, reports and PDF/CSV/XLSX exports.
- Geography/PostGIS, TimescaleDB, Celery jobs, offline sync/versioning, FHIR/HL7,
  forecasting/optimization service contracts, weather/population and backups.

No production migration, Git commit, push or deployment is performed by this setup.
