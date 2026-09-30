# Local team demo startup

Target agreed with the user: a local Docker demonstration, with contracts for
Members 2/3 while their actual integrations are unfinished. All added configuration
lives under `infra/`; the team scaffolds outside it are read as build inputs only.

## Prerequisites

On September 30, Docker Desktop was installed per-user from the official,
signature-verified Docker Inc installer. Docker CLI 29.8.1 and Compose v5.5.1
responded successfully. WSL installation succeeded, and enabling Windows Virtual
Machine Platform returned 3010 (restart required). Restart Windows, open Docker
Desktop, complete its first-launch prompts, and check `docker info` before startup.
No container build or deployment has been verified yet.
The pre-restart processor query reported firmware virtualization disabled and
Docker engine info failed. Recheck after restarting; if WSL still reports disabled
virtualization, enable Intel VT-x/AMD SVM in BIOS/UEFI before retrying.
Use the official [Docker Desktop Windows installation guide](https://docs.docker.com/desktop/setup/install/windows-install/).

From `infra/`, provision an unexpired local credential bundle if absent, and generate
the new team's Compose environment once:

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local provision
.\.venv\Scripts\python.exe deployment/prepare_local_env.py
```

Both refuse to overwrite existing files. `prepare_local_env.py` writes random
hexadecimal database/JWT secrets to an ignored, access-restricted `infra/.env` without
printing them. Keep a secure copy. Do not regenerate the database password after
the persistent PostgreSQL volume has been initialized: PostgreSQL will retain
its original password. Use controlled database credential rotation instead.

If using an older certificate bundle without monitor credentials, follow the
monitoring guide's fresh-bundle procedure and override every credential mount
consistently. On this host the local-dev bundle and restricted `infra/.env` were
generated already; do not rerun provisioning over them. Certificates expire October
7, 2026. Access was granted to the actual desktop user as well as the provisioning
sandbox identity. Run future provisioning from your own terminal so permissions
are assigned to your Windows account.

## Start team scaffolds plus federation

```powershell
docker compose -f compose.yaml -f compose.team.yaml config --quiet
docker compose -f compose.yaml -f compose.team.yaml up --build -d --wait --wait-timeout 180
```

Services: frontend at `http://127.0.0.1:8080`, backend at
`http://127.0.0.1:8000`, PostgreSQL on loopback 5432, internal Redis and federation
on loopback 8443 with mutual TLS. Frontend SPA routes use a local Nginx fallback;
its API URL is baked into the build. Backend health currently proves only its
scaffold responds, not that business routes/migrations or database queries work.
The root backend presently exposes its health scaffold; missing Member 2/3 routes
are not fabricated by Compose. This is local development, not a hardened production
application deployment. Redis has no password and is reachable inside the Compose
network; do not expose this network to untrusted services.

An optional `deployment/start-local.ps1 -Team -Monitoring -Grafana` wraps quiet
configuration validation and startup, checking Docker availability first. If the
machine blocks PowerShell scripts, use the direct Docker commands; do not change
execution policy just for this helper.

## Add monitoring and demo clients

Follow [monitoring](federated-monitoring.md) and [Grafana](federated-grafana.md) for
the monitor certificate and password file. Then use all files consistently:

```powershell
docker compose -f compose.yaml -f compose.team.yaml -f compose.monitoring.yaml -f compose.grafana.yaml up --build -d --wait
$env:FEDERATION_CLIENT_ROUNDS = '3'
docker compose -f compose.yaml -f compose.team.yaml -f compose.monitoring.yaml -f compose.grafana.yaml --profile training up -d
```

The privacy prototype runs separately with no network:

```powershell
docker compose -f compose.yaml run --rm --no-deps federation-privacy-demo
```

Inspect actual service logs, authenticated metrics, dashboard rendering and client
round outputs. Run the [database recovery drill](local-database-recovery.md) before
claiming backups are verified. CI activation still requires a team change outside
`infra/` and actual scanner runs. Alert delivery is not configured.

Stop with the same `-f` arguments and `down`, without `--volumes`, to preserve
database/Redis/model state. Grafana and Prometheus memory-only data disappear as
documented. No command here automatically deletes a persistent volume.

The combined four-file configuration passed `docker compose config --quiet`.
Static Compose/Python checks are not runtime evidence: Docker build/startup,
PostgreSQL restore and monitoring rendering are still pending on a prepared host.
