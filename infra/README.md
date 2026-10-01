# Sanjeevani — Member 4 Setup Guide

Step-by-step setup for the optimization, federated-learning, Docker, monitoring
and recovery implementation on branch **infra/ayan**.

All Member 4 code lives inside `infra/`. This guide uses **Windows PowerShell,
Python 3.12 (64-bit), and Docker Desktop with Linux containers**. Run project
commands from `infra/`, not the repository root.

> This is a local synthetic demonstration. Real business APIs and trained models
> remain Member 2/3 integrations. Existing security findings prevent a production
> readiness claim. Recommendations do not automatically move medical resources.

## 1. Install requirements

| Requirement | Official installation link |
| --- | --- |
| Git | https://git-scm.com/downloads/win |
| Python 3.12, 64-bit | https://www.python.org/downloads/windows/ |
| Docker Desktop | https://docs.docker.com/desktop/setup/install/windows-install/ |

Configure Docker Desktop for the WSL 2 backend and Linux containers. Complete
any requested restart, open Docker Desktop, and wait for its engine to run.
You do not need host installations of PostgreSQL, Redis, Node.js or Go, or a GPU.
Allow several GB of disk space and internet access for initial downloads/builds.

Verify in a new PowerShell terminal:

```powershell
git --version
py -3.12 --version
docker version
docker compose version
docker info
```

`docker info` must reach the server, not just display a client version.

## 2. Clone this branch

After the branch owner pushes the latest implementation:

```powershell
git clone --branch infra/ayan https://github.com/arpbiswas04-coder/Sanjeevani---Health-for-a-Better-Tomorrow.git
cd Sanjeevani---Health-for-a-Better-Tomorrow
cd infra
```

For an existing clone, from its repository root:

```powershell
git status
git fetch origin
git switch infra/ayan
git pull --ff-only origin infra/ayan
cd infra
```

If there is no local branch, use `git switch --track origin/infra/ayan` instead.
Preserve your uncommitted work before switching branches.

A clone cannot include uncommitted/unpushed files. If files such as
`compose.alerts.yaml` are missing, ask the branch owner to publish the latest
implementation. Do not copy another PC's virtual environments, secrets or volumes.

## 3. Create separate Python environments

OR-Tools and Flower have conflicting protobuf requirements. Do not combine the
two environments. From `infra/`:

```powershell
# Optimization
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[transport]"
.\.venv\Scripts\python.exe -m pip check

# Federation, credential generation and recovery
py -3.12 -m venv .venv-federated
.\.venv-federated\Scripts\python.exe -m pip install --upgrade pip
.\.venv-federated\Scripts\python.exe -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv-federated\Scripts\python.exe -m pip install -e ".[federation]"
.\.venv-federated\Scripts\python.exe -m pip check
```

Stop if installation fails. Dependencies are specified in
[pyproject.toml](pyproject.toml). Explicit executable paths avoid activation scripts.

## 4. Generate credentials — first setup only

Run under your own Windows account:

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local provision
.\.venv\Scripts\python.exe deployment/prepare_local_env.py
.\.venv-federated\Scripts\python.exe deployment/prepare_demo_secrets.py
```

| Generated location | Purpose |
| --- | --- |
| `.env` | Database and JWT credentials |
| `federated/secrets/local-dev/` | Federation/client/monitor certificates and admission keys |
| `federated/secrets/local-dev/grafana-admin-password` | Grafana password |
| `federated/secrets/local-dev/metrics-token` | Protected backend metrics token |
| `federated/secrets/local-dev/backup.key` | Backup decryption key |

These files are ignored by Git. Never commit or share them. Keep the backup key
recoverable and separate from archives.

The first two commands refuse overwrites: skip them on later starts. Never
regenerate the database password after its volume is initialized. The third
command adds only missing secrets. Certificates expire after seven days; renewal
needs a fresh bundle and consistent updates to all relevant Compose mounts.
Changing a bundle name alone does not change Compose's `local-dev` paths.
See [credential setup](docs/federated-local-setup.md) and
[monitoring setup](docs/federated-monitoring.md).

## 5. Build and start Docker services

From `infra/`, define these variables in PowerShell. Repeat this block in any
new terminal before using `$Docker` and `$Compose`:

```powershell
$Docker = (Get-Command docker -ErrorAction SilentlyContinue).Source
if (-not $Docker) {
    $Docker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'
}
if (-not (Test-Path -LiteralPath $Docker)) {
    throw 'Docker executable not found. Check installation and PATH.'
}
$Compose = @(
    'compose',
    '-f', 'compose.yaml',
    '-f', 'compose.team.yaml',
    '-f', 'compose.monitoring.yaml',
    '-f', 'compose.grafana.yaml',
    '-f', 'compose.observability.yaml',
    '-f', 'compose.alerts.yaml'
)
& $Docker info
& $Docker @Compose config --quiet
```

Continue only if those checks succeed:

```powershell
& $Docker @Compose up --build -d --wait --wait-timeout 180
& $Docker @Compose ps
```

The first build takes time to download dependencies and build the frontend,
backend, federation and patched Alertmanager. Build tools run inside Docker.
Nine persistent services start: frontend, backend, PostgreSQL, Redis, federation
server, Prometheus, Grafana, Alertmanager and the local alert receiver.

Alternatively, after setup:

```powershell
.\deployment\start-local.ps1 -Alerts -Grafana
```

If PowerShell blocks scripts, use the direct Docker commands above. You do not
need to change the machine's execution policy. Training clients start separately.

## 6. Open the applications

| Service | Address |
| --- | --- |
| Frontend | http://127.0.0.1:8080 |
| Backend health | http://127.0.0.1:8000/api/v1/health |
| API documentation | http://127.0.0.1:8000/api/v1/docs |
| Grafana | http://127.0.0.1:3000 |
| Prometheus | http://127.0.0.1:9090 |
| Alertmanager | http://127.0.0.1:9093 |
| Local alert counts | http://127.0.0.1:9094/counts |
| Federation | https://127.0.0.1:8443 — client certificate required |

PostgreSQL uses local port 5432, database/user `sanjeevani`, and the password in
your private `.env`. Redis is only available inside the Docker network.

Grafana username is `admin`. Read your generated password privately:

```powershell
Get-Content .\federated\secrets\local-dev\grafana-admin-password
```

Do not share that output. Open the federation and application/infrastructure
dashboards. Prediction/optimizer panels stay empty until those operations run
inside the instrumented backend process; standalone CLI runs do not feed them.

Ports are loopback-only. Federation requires mutual TLS; a browser without a
certificate should fail. Do not disable TLS verification. Notifications go only
to the local receiver, not to email or an external service.

## 7. Verify the setup

Wait at least 15 seconds for a Prometheus scrape, then run:

```powershell
.\.venv-federated\Scripts\python.exe deployment/verify_local.py --observability --grafana
.\.venv-federated\Scripts\python.exe deployment/verify_local_alerts.py
```

Expected: all ten runtime checks pass; `firing_delivered` and
`resolved_delivered` are `true`. Evidence is saved under ignored `outputs/`.
The synthetic alert verifies the local delivery route, not every alert rule.

## 8. Run Member 4 demonstrations

### Optimization

```powershell
.\.venv\Scripts\python.exe delivery.py --demo
```

This runs ten bounded synthetic CLI demonstrations and saves a summary under
`outputs/delivery-*`. No real inventory or patient data is modified.

Individual examples:

```powershell
.\.venv\Scripts\python.exe -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json
.\.venv\Scripts\python.exe -m optimization.ambulance --demo
.\.venv\Scripts\python.exe -m optimization.emergency --demo
```

### Three regional federation clients

With the stack running and step 5 variables defined:

```powershell
$env:FEDERATION_CLIENT_ROUNDS = '3'
$env:FEDERATION_CLIENT_MAX_WAIT_SECONDS = '600'
& $Docker @Compose --profile training up -d federation-client-a federation-client-b federation-client-c
& $Docker @Compose logs -f federation-server federation-client-a federation-client-b federation-client-c
```

Allow several minutes; the default round interval is 120 seconds. A client
`submitted` result confirms admission, while server `aggregated` messages confirm
aggregation. Ctrl+C exits log viewing without stopping containers.
See [training runner](docs/federated-round-runner.md).

### Optional privacy demonstration

Only on a new, never-initialized privacy volume:

```powershell
& $Docker compose -f compose.yaml -f compose.privacy.yaml run --rm --no-deps federation-privacy-demo privacy --ledger federated/checkpoints/privacy.sqlite --initialize-ledger --rounds 1
```

For later runs:

```powershell
& $Docker compose -f compose.yaml -f compose.privacy.yaml run --rm --no-deps federation-privacy-demo
```

Never reset/delete the ledger to bypass its privacy budget. This separate,
network-isolated synthetic workflow does not automatically make the normal
HTTPS training path private. Read [privacy limitations](docs/federated-privacy.md).

## 9. Backup and recovery

With Docker running:

```powershell
# Synthetic database recovery into a NEW database
.\.venv-federated\Scripts\python.exe deployment/recovery_drill.py

# Encrypted configuration backup and verified fresh restore
.\.venv-federated\Scripts\python.exe deployment/config_backup.py

# Local team database backup and retention PLAN
.\.venv-federated\Scripts\python.exe deployment/backup_job.py --database sanjeevani --keep 7
```

Reports print their output directories. The drill creates isolated synthetic
databases and preserves the team database. Retention planning does not delete
backups. Keep the original encryption key; a replacement cannot decrypt old data.

For a same-PC copy, substitute the directory printed by `config_backup.py`:

```powershell
New-Item -ItemType Directory -Force outputs/backup-copy-demo | Out-Null
.\.venv-federated\Scripts\python.exe deployment/archive_copy.py --archive outputs/backups/YOUR_CONFIG_DIRECTORY/config.enc --destination outputs/backup-copy-demo --local-demo
```

This is not off-host disaster recovery. No external upload or scheduled task is
activated. See [operations](docs/operations-completion.md) and
[database recovery](docs/local-database-recovery.md).

## 10. Stop, restart and update safely

With the variables from step 5:

```powershell
# Stop containers; keep data
& $Docker @Compose --profile training stop

# Restart normal services
& $Docker @Compose up -d --wait --wait-timeout 180

# Remove containers/networks; retain named volumes
& $Docker @Compose --profile training down
```

**Do not add `--volumes` or `-v`, and do not prune volumes.** Volumes contain
application data, model checkpoints and privacy accounting. Temporary monitoring
history and local receiver counts may reset after container recreation.

To update code, preserve local changes, pull the agreed branch, return to `infra`
and repeat step 5's build/start command. Do not regenerate credentials.
See [deployment/rollback](docs/deployment-handoff.md).

## 11. Tests and CI

Tests are unnecessary for every normal startup. After code changes:

```powershell
.\ci-cd\check-local.ps1
# Also verify the running stack and local alerts:
.\ci-cd\check-local.ps1 -Runtime
```

If scripts are blocked, use:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s optimization/tests -q
.\.venv-federated\Scripts\python.exe -m unittest discover -s federated/tests -q
.\.venv-federated\Scripts\python.exe -m unittest discover -s monitoring/tests -q
```

`ci-cd/member4-ci.yml` is an inactive GitHub Actions template. Activation requires
an authorized root `.github/workflows/` change. Local tests do not replace image
or dependency scans. See [security scanning](docs/security-scanning.md).

## Troubleshooting

| Problem | Check/action |
| --- | --- |
| Python not found | Install Python 3.12 and reopen PowerShell. |
| Docker engine unavailable | Open Docker Desktop; check Linux containers, WSL and requested restart. |
| Wrong Python module | Run from `infra/` with the correct environment executable. |
| Dependency conflict | Keep federation and optimizer dependencies separate. |
| Existing credential files | Skip first-time provisioning; do not delete/regenerate secrets. |
| Permission denied | Provision from your own account; check Docker file access without making keys public. |
| Expired certificates | Follow the fresh-bundle/mount procedure; do not disable TLS. |
| Database authentication fails | Check whether `.env` changed after initialization; preserve the volume. |
| Port conflict | Check 3000, 5432, 8000, 8080, 8443 and 9090–9094. |
| First monitoring check fails | Wait for a scrape interval, inspect Targets/logs, then retry. |
| Insufficient federation participants | Start all three clients. Idle rounds without clients are expected. |
| Empty prediction panels | Actual backend model inference has not supplied observations. |
| Privacy budget exhausted | Stop and review policy; never reset accounting. |
| Build failure | Check internet/disk space and the first failing build step; do not remove pins blindly. |

Read-only diagnostics:

```powershell
& $Docker @Compose ps
& $Docker @Compose logs --tail 80 app-backend federation-server prometheus alertmanager alert-receiver
```

Never share secrets or real health data in diagnostics. macOS/Linux/ARM require
platform-specific paths, compatible wheels and reviewed UID/mount permissions;
this guide documents the verified Windows/Linux-container setup.

## Teammate integration references

- [Member 2/3 contracts](docs/team-integration-contracts.md)
- [Backend inventory handoff](docs/backend-handoff.md)
- [Application monitoring](docs/application-monitoring.md)
- [Regional onboarding](docs/regional-onboarding.md)
- [Current release status](docs/local-release-status.md)
- [Federation security findings](docs/security-findings.md)
- [Backend security findings](docs/backend-security-findings.md)
- [Alertmanager remediation](docs/alertmanager-security-findings.md)

## Current limitations

Real APIs/models remain teammate integrations. Backend/federation vulnerabilities
remain production release blockers. Cloud deployment, hosted Member 4 CI,
external notification delivery and real off-host storage are not activated.
The patched Alertmanager's recorded HIGH/CRITICAL scan passed; this is not a
blanket security guarantee. Use synthetic data for this local demonstration.
