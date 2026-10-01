# Federation Grafana dashboard

The optional Grafana overlay provisions the **Sanjeevani / Sanjeevani Federation**
dashboard and a fixed Prometheus datasource. Eight panels show authenticated scrape
availability, model version, update admission rates, last recorded node status,
round outcomes, aggregation duration, checkpoint age and firing Prometheus alerts.
Missing metrics display as missing data, not a healthy zero.

## Prepare login

First complete [local credential setup](federated-local-setup.md) and
[Prometheus setup](federated-monitoring.md), including the monitoring certificate.
From `infra/`, create an admin password file inside the existing restricted
`local-dev` bundle. The following PowerShell commands prompt without echoing the
password. Choose a strong unique password; do not use an empty value.

```powershell
$grafanaPassword = Read-Host 'New local Grafana admin password' -AsSecureString
if ($grafanaPassword.Length -lt 16) { throw 'Use at least 16 characters' }
$grafanaPasswordFile = Join-Path (Get-Location) 'federated/secrets/local-dev/grafana-admin-password'
if (Test-Path -LiteralPath $grafanaPasswordFile) { throw 'Password file already exists; use the existing login' }
[System.IO.File]::WriteAllText($grafanaPasswordFile, ([pscredential]::new('admin', $grafanaPassword)).GetNetworkCredential().Password)
$grafanaPassword.Dispose()
Remove-Variable grafanaPassword
```

The file contains plaintext and inherits the bundle's restricted Windows ACL.
On native Linux, create it privately inside the existing restricted bundle and
set file mode 0600. Match `MEMBER4_UID` to its owner. The file is Git-ignored and
excluded from image builds. Grafana mounts only this password file, not federation
node keys or certificates. No password is generated or retained by implementation
validation.

## Start

Use all three Compose files in order:

```powershell
docker compose -f compose.yaml -f compose.monitoring.yaml -f compose.grafana.yaml config --quiet
docker compose -f compose.yaml -f compose.monitoring.yaml -f compose.grafana.yaml up --build -d
```

Open `http://127.0.0.1:3000`, sign in as `admin` with your chosen password, then open
**Dashboards → Sanjeevani → Sanjeevani Federation**. Wait for Prometheus's first
scrapes. Training clients remain on-demand; see the Docker guide for their commands.

The datasource uses `http://federation-server:9090` because Prometheus shares that
container's network namespace. Grafana connects over the private Compose network.
The coordinator-to-Prometheus scrape remains mutually authenticated HTTPS.

## Persistence and access

- Grafana is published only on host loopback port 3000. Login is required;
  anonymous access and public sign-up are disabled. This local HTTP UI is not a
  production HTTPS deployment.
- Grafana's database is temporary memory. Stopping the container loses sessions,
  created users and UI preferences. On restart, the password file initializes the
  admin account again and the dashboard is reprovisioned from source.
- Dashboard edits should be made in
  `monitoring/grafana/dashboards/federation.json`; provisioned UI editing is disabled.
- Changing a password file while Grafana is running does not update its database.
  Restart this ephemeral development instance to initialize from the new file.
- Prometheus still has its separate localhost UI without login. Grafana login does
  not add authentication to Prometheus. Containers on the shared network can also
  reach its API. External alert delivery is not configured.

Stop with the same three files and omit `--volumes` to preserve model checkpoints:

```powershell
docker compose -f compose.yaml -f compose.monitoring.yaml -f compose.grafana.yaml down
```

On September 30 the container started, authenticated dashboard API returned its
expected UID and eight panels, and the Prometheus federation scrape was healthy.
Visual dashboard rendering remains uninspected. Image tags are versioned but not
digest-locked; monitoring-image scans and production release hardening remain separate work.

References: [Grafana file provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
and [Docker configuration / file-based secrets](https://grafana.com/docs/grafana/latest/setup-grafana/configure-docker/).
