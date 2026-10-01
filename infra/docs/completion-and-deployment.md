# Member 4 implementation and deployment guide

Branch: `infra/ayan`. Updated October 1, 2026. This page supplements the
[step-by-step local setup](../README.md). The latest request authorizes root
GitHub Actions definitions as well as infra changes. Nothing has been pushed or
deployed to an external host by this implementation session.

## Completion matrix

| Area | Implemented | Verification / boundary |
| --- | --- | --- |
| Optimization, emergency priorities, simulation and resilience | Existing engines retained | 116 tests; recommendations require human approval |
| Federation, checkpoints, signed HTTPS updates | Existing reference and Flower/PyTorch adapters retained | 40 federation tests including subprocess training |
| Configurable DP | Client-level clipping, Gaussian noise, budget cap and durable accounting | Synthetic two-coordinate model; finite-precision mechanism is not independently audited |
| Authenticated masked aggregation | Ed25519-pinned identities, signed ephemeral X25519 keys and updates, context binding and replay rejection | Fixed roster, abort on dropout; trusted in-process demonstration |
| Personalization | Optional node-local fine-tuning, global model preserved | Synthetic client; personalized parameters stay local and are not submitted |
| Region/country metadata | Bounded public registry and regional-runner integration | Single-level coordinator; cross-country transport/governance is not deployed |
| TLS ingress | HTTPS, redirect, headers, bounded bodies, separate route limits and explicit CORS | 11 local acceptance checks passed with certificate verification |
| Secrets | Ignored restricted credentials, file injection and service-specific mounts | External secret-manager agent/role provisioning remains operator work |
| CI | Root checks, dependency/image scans, report artifacts, exact-revision release gate | Definitions present; hosted execution requires reviewed commit/push |
| Deployment | Guarded SSH/Compose staging and production workflow, readiness, prior-release rollback | Linux host mechanics tested with mocked Docker/HTTPS; no remote deployment attempted |
| Monitoring | Authenticated metrics, liveness/readiness, backup/restore status and alerts | Ten runtime checks; two dashboards loaded; visual dashboard review not performed |
| Recovery | Encrypted backup, fresh database restore, config restore and storage adapters | Real synthetic PostgreSQL recovery passed; S3 transport tested with a mock |
| Production release | Blocked | Known security findings, external setup and real Member 2/3 integration remain |

## Local HTTPS setup

First complete README sections for both Python environments, Docker, the local
credential bundle, generated `.env`, and monitoring/backup secrets. Keep existing
credentials, privacy ledgers and volumes. From `infra`, create the new ingress
identity once, under the same Windows user that runs Docker Desktop:

```powershell
.\.venv-federated\Scripts\python.exe security/prepare_ingress.py
.\deployment\start-local.ps1 -Https
.\.venv-federated\Scripts\python.exe deployment/verify_ingress.py
.\.venv-federated\Scripts\python.exe deployment/verify_local.py --observability --grafana
.\.venv-federated\Scripts\python.exe deployment/verify_local_alerts.py
```

Do not repeat certificate generation if the `ingress` directory already exists.
Open `https://localhost:9443`; local certificates are self-signed and expire in
seven days. The verifier trusts only the generated certificate and validates its
hostname; it never disables verification. No OS/browser trust store is modified.
HTTP port 9080 redirects to HTTPS. Existing direct demo ports remain loopback-only.
The frontend is rebuilt with the HTTPS API origin by the overlay.

If an automation account generated the files, grant only your Docker Desktop
account read access to that directory using its actual identity; never grant
Everyone access or post a private key. On Linux, the containers use UID 1000;
provision the secret files for that UID with owner-only access. Host tools must
run as the same authorized owner or through controlled administration.

`/api/v1/live` checks the running application wrapper. `/api/v1/ready` returns 200
only when bounded PostgreSQL and Redis probes succeed; failures return sanitized
503 JSON. Neither endpoint validates a clinical model or business workflow.
`/internal/metrics` is hidden at ingress. `/metrics/` requires the pinned monitor
certificate identity and the existing metrics bearer token. Federation's own
endpoint independently enforces its monitor identity.

Limits default to auth/admin 5 requests/minute, optimization/recommendations
2/second, general API 20/second and metrics 2/second, with bounded bursts. They
are per source IP, not a substitute for Member 2 authentication/authorization.
The proxy overwrites forwarded-address headers. Do not add an untrusted upstream
proxy or trust arbitrary forwarded headers without reviewing rate-limit identity.

## Learning configuration and boundaries

`federated/configs/learning.json` contains `privacy.enabled`, `clipping_norm`,
`noise_multiplier`, `delta`, `privacy_budget`, and personalization `enabled`,
`local_epochs`, `learning_rate`. Unknown/malformed fields are rejected before
training. Privacy defaults on; personalization defaults off. Do not claim privacy
for a run with DP disabled. Disabled runs report no privacy budget estimate.

```powershell
.\.venv-federated\Scripts\python.exe -m federated.privacy --rounds 1
# Durable accounting: only for a NEW ledger, initialize once.
.\.venv-federated\Scripts\python.exe -m federated.privacy --ledger federated/checkpoints/member4-private.sqlite --initialize-ledger --rounds 1
# Later runs keep the same ledger and omit --initialize-ledger.
.\.venv-federated\Scripts\python.exe -m federated.privacy --ledger federated/checkpoints/member4-private.sqlite --rounds 1
```

The parent checkpoint directory must exist. Never reset, copy back an old ledger
or change policy to evade an exhausted budget. Charges happen before release and
are not refunded on aggregation failure. Keep the ledger backed up securely with
rollback controls before considering real data. The process cannot protect its
ledger against an administrator rolling back storage.

Signed packets bind node, fresh nonce, round and global-model version. Every node
verifies the same signed roster before masking. All members must participate;
missing/duplicate/unknown nodes, altered signatures and replay abort. Production
would need independent identity enrollment, process/host isolation, an audited
protocol and explicit dropout/collusion policy. The plain FedAvg, Flower adapter
and HTTPS runner do **not** automatically gain DP or masking from this demo.

Personalization copies the global model before local training and returns a
node-local result. The demo reports only enabled-node counts, never personalized
weights or private training losses. Integrate a real Member 3 model through its
reviewed adapter rather than treating the synthetic model as healthcare AI.

`federated/configs/regions.json` maps node IDs to public region and two-letter
country identifiers. Country metadata is not a legal transfer permission or
authentication grant. Enrollment must separately provision trusted node keys.
Hierarchy: country/region metadata -> registered nodes -> one coordinator ->
global model -> optional local fine-tuning. Multi-tier aggregation is not claimed.
No patient-level data belongs in the registry.

## Secrets and trust

Use GitHub Environment secrets for deployment SSH keys and host pins; use a host
secret manager/agent or workload identity to materialize service secret files.
The backend wrapper accepts `JWT_SECRET_FILE`, `JWT_REFRESH_SECRET_FILE`,
`POSTGRES_PASSWORD_FILE`, `DATABASE_URL_FILE` and `REDIS_URL_FILE`. Set exactly one
of a variable and its `_FILE` form; remove the conflicting Compose environment
entry in a reviewed host override. Files are bounded and never printed. Direct
injection into the process environment is supported by the current local Compose
configuration; keep Docker-host/admin access restricted because environment
values can be inspected by administrators. No Vault or cloud account is created.

Only node-specific mounts go to federation clients; the coordinator and monitor
have different identities. PostgreSQL and Redis are private on the Compose
network in the public overlay. This is not encryption of every internal service
link. Protect the host/network; stronger east-west TLS remains deployment-specific.
Rotate using newly provisioned identities and coordinated mounts, not by deleting
the active bundle. The local CA is intentionally unsuitable for production.

## Backup, object storage and recovery

```powershell
.\.venv-federated\Scripts\python.exe deployment/backup_job.py
.\.venv-federated\Scripts\python.exe deployment/recovery_drill.py
.\.venv-federated\Scripts\python.exe deployment/config_backup.py
```

The first command backs up the application database encrypted. The drill creates
synthetic source/restore databases, compares rows and constraints, and preserves
the originals. It proves database mechanics, not recovery of unimplemented real
application transactions. The configuration backup explicitly excludes secrets.
Back up keys separately under a different access policy; losing a key loses the
encrypted backup. Preserve checkpoint/privacy state and document consistent
recovery separately from a database dump. See [existing recovery runbook](backup-recovery.md).

Storage adapter commands read process environment variables. They support a
bounded encrypted archive up to 96 MiB, immutable upload names, SHA-256 readback,
download, listing and retention planning. Install S3 support only when needed:

```powershell
.\.venv-federated\Scripts\python.exe -m pip install ".[backup]"
$env:BACKUP_STORAGE_MODE = 's3'
$env:S3_BUCKET = 'YOUR-PROVISIONED-BUCKET'
# Set S3_ENDPOINT only for an HTTPS S3-compatible service.
# Use workload identity or the standard AWS credential/profile chain.
.\.venv-federated\Scripts\python.exe -m deployment.store_backup upload --file outputs/backups/YOUR-JOB/postgres.enc --key UNIQUE-BACKUP.enc
.\.venv-federated\Scripts\python.exe -m deployment.store_backup list
.\.venv-federated\Scripts\python.exe -m deployment.store_backup download --key UNIQUE-BACKUP.enc --sha256 TRUSTED-MANIFEST-SHA256 --file outputs/downloaded-backup.enc
.\.venv-federated\Scripts\python.exe -m deployment.store_backup retention-plan --days 30
```

Replace the uppercase placeholders; upload verifies the sibling `manifest.json`.
For local adapter testing choose `BACKUP_STORAGE_MODE=local` and an existing
`BACKUP_LOCAL_DIRECTORY`. A local directory is not off-host recovery. Restrict S3
permissions to the dedicated `sanjeevani-backups/` prefix; no public ACLs. Object
locking/versioning/lifecycle and external service compatibility require operator
setup. The adapter requires conditional writes (`If-None-Match: *`). Keep the
trusted checksum independently of downloaded bytes. After download, perform an
actual decrypt/restore drill with the separate backup key. No real bucket was used.

Retention outputs a deletion plan only. The programmatic cleanup method requires
an explicit reviewed key list and confirmation; schedulers never delete archives.
Schedule `backup_job.py` daily and a restore drill weekly using the host scheduler,
with the correct working directory/environment and restricted account. No machine
schedule has been installed. Agree real RPO/RTO before production; 24-hour backup
and seven-day restore-age alerts are demonstration thresholds.

Backup/restore CLIs atomically write sanitized status under `outputs/operations`.
Metrics preserve the last successful timestamp after a failed attempt. Missing or
corrupt evidence reports unavailable, never healthy zero. The backend mounts this
directory read-only. Prometheus alerts on missing/stale/failed evidence and
optimizer failures. Configure a real external Alertmanager receiver separately;
the local receiver proves only local firing/resolved delivery.

## CI and guarded remote deployment

Root `.github/workflows/member4-ci.yml` is the authoritative definition; the copy
under `infra/ci-cd` is a reference only. Existing Backend/Frontend CI are reused.
Checks run on PRs to main/develop and pushes including infra/ayan; security jobs
fail on findings and retain reports. No ignore list or `continue-on-error` bypass
was added. Frontend has no existing lint/test script, so those optional steps do
not constitute frontend test coverage; its production build is checked.

The deploy workflow supports the explicit `ssh-compose` provider on a
pre-provisioned Linux host. It does not create cloud infrastructure. Staging can
run after Member 4 checks for a develop push; manual deployment accepts main or
develop, with production restricted to main. Every deployment requires successful
Member 4, Backend, Frontend and Project Integrity workflow runs for the exact SHA.
If another check is still running, deployment fails closed; rerun after it passes.
Workflow-run triggers require the deploy definition on the repository's default
branch. A PR cannot deploy. Configure required reviewers and allowed branches on
both GitHub Environments before providing credentials.

Create GitHub Environments `staging` and `production`, each with:

| Kind | Names |
| --- | --- |
| Variables | `DEPLOY_PROVIDER=ssh-compose`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH` |
| Secrets | `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS` |

Verify SSH host-key fingerprints independently; the client uses strict checking
and never runs automatic `ssh-keyscan`. Use a dedicated deployment account/path,
Python 3.12+, Docker and a modern Compose supporting `!reset` / `!override`.
Use separate staging and production hosts because public ports and image tags
are shared. Docker access is privileged host access; protect that account.

On each host prepare the following before enabling its workflow:

```text
/srv/sanjeevani/<environment>/
  shared/
    .env                         # owner-only, plain KEY=value (no shell/quoted syntax)
    federated-secrets/local-dev/  # service-specific production-issued identities
    outputs/operations/          # persistent scheduler evidence/config backup output
    checkpoints/                 # persistent host-side demo/accounting state
  incoming/                      # uploaded exact-commit Git archives
  releases/                      # separate extracted source tree per commit
```

The shared environment needs generated `MEMBER4_DB_PASSWORD`, JWT secrets, a valid
`PUBLIC_HTTPS_ORIGIN=https://your-host.example`, matching explicit JSON
`CORS_ALLOWED_ORIGINS`, and absolute `NGINX_TLS_DIRECTORY` / `NGINX_CONFIG` paths.
TLS directory contains `cert.pem` (full chain) and `key.pem`, issued for that host.
Protect private keys; provision read access only for the authorized container UID.
The seven-day local generator is not production certificate provisioning.

Render the host Nginx config from reviewed source, with the intended origin and
optional `NGINX_AUTH_RATE`, `NGINX_OPERATIONS_RATE`, `NGINX_API_RATE` in process env:

```bash
cd infra
PUBLIC_HTTPS_ORIGIN=https://your-host.example python3 deployment/render_ingress.py
```

Copy the generated non-secret `outputs/nginx.conf` to the absolute configured host
path, run Nginx validation as part of the container deployment, and configure
certificate renewal/reload through the chosen issuer. Allow inbound 443 and the
HTTP redirect port 80 only as needed; direct database/API/monitoring ports are
removed by `compose.production.yaml`.

Deployment uploads an exact-commit archive, validates Compose, builds/starts it,
waits for container health and verifies HTTPS `/api/v1/ready`. Source releases are
immutable and existing data volumes are retained. A failure redeploys the previous
source revision if a prior success pointer exists. It does not undo database
migrations; none are applied. Initial deployment failure has no prior revision to
restore. Mutable upstream image tags prevent a bit-identical rebuild guarantee;
pin reviewed digests/artifacts before a real release. A failed SHA directory is
preserved for inspection and is not overwritten on retry. Review/rename it or
deploy a newly reviewed commit. Host-side firewall, DNS, TLS, external alerts and
real storage remain owner responsibilities.

## Evidence and developer handoff

From `infra`:

```powershell
.\ci-cd\check-local.ps1 -Runtime
.\.venv-federated\Scripts\python.exe deployment/verify_ingress.py
.\.venv\Scripts\python.exe -m ruff check --select E9,F63,F7,F82 optimization federated deployment security monitoring
.\.venv-federated\Scripts\python.exe security/check_tracked_secrets.py
.\.venv-federated\Scripts\python.exe delivery.py
```

Install Ruff in `.venv` before its first use. Linux-only deployment filesystem
tests skip on Windows; they run in Linux CI and were also exercised in a local
Linux container. `delivery.py` inventories actual reports and distinguishes
missing/stale evidence from passing evidence. Local reports do not prove hosted
CI, current-source certification or production readiness. Security reports remain
release blockers even when functional tests pass.

For coding assistants: work from `infra`, read the root workflows and this guide,
preserve uncommitted teammate work and ignored runtime state, use separate
optimizer/federation environments, and run focused tests for the changed subsystem.
Never generate secret values in a tracked file, reset accounting, bypass scanner
failures, fabricate model metrics, or execute medical recommendations. Integrate
Member 2/3 using the [existing contracts](team-integration-contracts.md).
