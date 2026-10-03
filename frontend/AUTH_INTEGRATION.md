> Current status: see [Phase 5 readiness audit](../FINAL_READINESS_AUDIT.md) and [supported setup](../DEVELOPMENT.md). This report retains historical phase results. Phase 5 adds optional report-job idempotency (`ReportJobRequest`), real Celery worker/Beat verification, and explicit production API configuration. Earlier statements about those gaps are superseded.

# Frontend/backend authentication integration

Verified on `integration/frontend-backend`, 2026-10-02. No dependencies installed,
commits, pushes, or deployments. The pre-existing `frontend/package-lock.json`
change was preserved byte-for-byte.

## Contract and behavior

The contract was generated from the merged FastAPI application, not inferred from
older documentation. Its live schema is `GET /api/v1/openapi.json`.

| Endpoint | Contract used |
| --- | --- |
| `GET /api/v1/health` | Public liveness; does not prove database availability |
| `POST /api/v1/auth/login` | Form-encoded `username`, `password`, `grant_type=password`, optional `mfa_proof`; bare `access_token`, `refresh_token`, `token_type`, `expires_in` |
| `GET /api/v1/users/me` | Bearer authentication; `{success,data}` including identity, database roles, permissions, scope mode, facility/district IDs |
| `POST /api/v1/auth/refresh` | JSON `refresh_token`; `{success,data}` containing a rotated token pair |
| `POST /api/v1/auth/logout` | Bearer authentication; server revokes the user's sessions |
| `POST /api/v1/auth/password/reset/request` | JSON `username`; generic 202 response, not proof that delivery occurred |
| `GET /api/v1/users` | Protected verification endpoint; requires `admin.users` and global scope |

`/users/me` now derives grants from existing `users`, `roles`, `user_roles`,
`permissions`, `role_permissions`, `user_facilities`, and `user_districts` tables.
It does not disclose password hashes or token versions. No schema change or new
migration is needed. Database connection failures are sanitized 503 responses.

All backend HTTP traffic goes through `httpClient.ts`; protected calls use
`apiRequest`. Expiring access tokens rotate through the refresh endpoint; 401 is
retried once, while 403 never grants access or triggers privilege escalation.
Refresh requests share one promise per tab and use Web Locks across tabs when
available. A refresh failure ends the local session. Backend RBAC and scope checks
remain authoritative even if a user modifies browser state.

Only tokens and their expiry/persistence metadata are stored. Identity and grants
are fetched again on restoration and window focus. Session storage is the default;
remembering a terminal explicitly opts into local storage. Legacy demo sessions
are rejected. Logout clears local identity, tokens, and query cache even on an
outage, with a warning if remote revocation could not be confirmed. No demo login
fallback or generated demo token remains.

Role aliases select presentation only; permissions always come from the server:

| Backend names (case-insensitive) | Frontend role |
| --- | --- |
| `administrator`, `admin`, `super_admin` | `SUPER_ADMIN` |
| `national_admin`, `national_officer` | `NATIONAL_ADMIN` |
| `state_admin`, `state_officer` | `STATE_ADMIN` |
| `district_admin`, `district_officer` | `DISTRICT_ADMIN` |
| `facility_admin` | `FACILITY_ADMIN` |

An unsupported role or a selected role not actually assigned by the backend fails
closed. Role aliases never supply capabilities. Navigation and direct routes both
check explicit backend permissions; global administration also checks scope.
Accounts without dashboard permissions land on their real profile.

## Development configuration

Use an existing `backend/.venv` (create one before installing anything if missing).
Activate it and verify `python` resolves inside that directory before installing
requirements. No packages were installed during this change.

Provide backend `DATABASE_URL` for a migrated PostgreSQL database and a private
`JWT_SECRET` of at least 32 characters in the backend environment. Apply existing
migrations using `python -m alembic upgrade head`. Provision a real account using
`python -m app.bootstrap` or existing administration APIs. The bootstrap creates
an `administrator` with explicit capabilities and global scope. Other accounts
need assigned roles, capabilities, and facility/district scopes as appropriate.
Production also requires configured Redis and explicit CORS origins.

Set `VITE_BACKEND_URL=http://localhost:8000` in `frontend/.env.local` if needed;
see `.env.example`. Never put signing secrets in `VITE_*` variables. Backend CORS
must include the actual frontend origin; defaults include `http://localhost:5173`
and `http://127.0.0.1:5173`. Use HTTPS outside local development.

Documented commands used for verification:

```powershell
# backend, with backend/.venv active
python -m uvicorn app.main:app --reload --port 8000
# frontend, separate terminal
npm run dev -- --port 5173 --strictPort
```

MFA requires a working backend provider. The sign-in form forwards optional proof;
the separate MFA screen no longer fabricates verification. Recovery requests use
the real endpoint, but delivery requires the backend recovery adapter. Neither
screen promises successful verification or delivery without backend evidence.

## Verification results and limits

| Check | Result |
| --- | --- |
| `backend/.venv/Scripts/python.exe -m pytest -q -rs` | 75 passed, 5 skipped, 1 existing Starlette/httpx deprecation warning |
| `npm test` | 61 passed, 3 opt-in live tests skipped in the default run |
| `npm run build` | Passed TypeScript and Vite; large-chunk warning remains |
| `python -m alembic heads` | One head: `c83d9e124a35` |
| `python -m alembic check` | No new upgrade operations, against the isolated migrated SQLite database |
| Live health / OpenAPI / login / current user / users / logout | 200; logged-out JWT then rejected with 401 |
| Live frontend component, backend running | 2 passed: real form login/JWT/profile/protected call/refresh/logout and invalid/demo credentials |
| Live frontend component, backend stopped | 1 passed: visible network error and no authenticated session |

The live tests render the actual React login component in jsdom and make real HTTP
requests; they do not mock fetch or the backend. They are **not browser E2E tests**.
The browser tool reported no available browsers, so actual-browser interaction
and browser enforcement of CORS/storage remain unverified. The Vite page itself
returned 200, and backend CORS preflight is covered by regression tests.

No PostgreSQL server was listening locally. Live verification used a newly
migrated, isolated SQLite database and temporary account, without changing any
existing database or `.env`. Four backend skips require a disposable PostgreSQL/
PostGIS `TEST_DATABASE_URL` ending `_test`; the fifth additionally requires
TimescaleDB and `ENABLE_TIMESCALEDB=1`. PostgreSQL integration remains to be run.
SQLite migration setup emitted the existing unnamed-CHECK reflection warning.

To repeat live frontend tests against a disposable running backend with a real
global administrator, set these variables in the frontend terminal:

```powershell
$env:AUTH_LIVE_TEST='1'
$env:AUTH_LIVE_USERNAME='<temporary administrator username>'
$env:AUTH_LIVE_PASSWORD='<temporary password>'
npm test -- src/test/authLive.integration.test.tsx
# Stop the disposable backend, then run the outage case:
$env:AUTH_LIVE_OUTAGE='1'
npm test -- src/test/authLive.integration.test.tsx
```

Running mode executes two tests and skips the outage case; outage mode executes
one test and skips the two running-backend cases. All three were executed across
these modes. Existing resource dashboards still contain prototype data; wiring
those unrelated modules was outside this authentication change.

## Files changed

Paths below are relative to the repository root; `frontend/package-lock.json`
is deliberately excluded because its existing change belongs to the user.

- Backend: `backend/app/api/v1/endpoints/identity.py`, `backend/app/services/identity.py`,
  `backend/app/schemas/outputs.py`, `backend/app/core/database.py`.
- Frontend client/state/types: `frontend/src/services/httpClient.ts`,
  `frontend/src/services/authService.ts`, `frontend/src/services/api.ts`,
  `frontend/src/store/authStore.ts`, `frontend/src/types/auth.ts`.
- Routing/navigation: `frontend/src/app/App.tsx`, `frontend/src/app/router.tsx`,
  `frontend/src/app/authorization.ts`, `frontend/src/components/common/RoleGuard.tsx`,
  `frontend/src/components/common/ProtectedRoute.tsx`, `frontend/src/components/common/RoleSidebar.tsx`.
- Auth screens: `frontend/src/modules/auth/LoginPage.tsx`, `frontend/src/modules/auth/ProfilePage.tsx`,
  `frontend/src/modules/auth/MFAPage.tsx`, `frontend/src/modules/auth/ForgotPasswordPage.tsx`.
- Tests: `backend/tests/test_frontend_auth_contract.py`, `frontend/src/test/authRoleRouting.test.tsx`,
  `frontend/src/test/authLive.integration.test.tsx`, `frontend/src/test/blueprintPhases.test.tsx`,
  `frontend/src/test/member1Deliverables.test.tsx`.
- Configuration/docs: `frontend/.env.example`, `frontend/AUTH_INTEGRATION.md`.

Before considering browser integration verified: run the actual browser login/
outage flow and the PostgreSQL-backed integration checks. Configure real account
assignments and backend secrets/database access for your development environment.
