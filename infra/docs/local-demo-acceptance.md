# Local demo acceptance — September 30, 2026

All changes stay under `infra/`; root application sources are build inputs.
The agreed target is a local demonstration while Member 2 APIs and Member 3
trained artifacts remain unavailable.

## Observed runtime evidence

- Docker engine 29.8.1 started and Compose built frontend, backend and federation images.
- PostgreSQL, Redis, backend health endpoint, frontend SPA fallback and federation listener ran.
- Three separately authenticated PyTorch clients each submitted three rounds and exited zero.
  Server logs confirmed rounds 1, 2 and 3 aggregated; submission alone was not counted as aggregation.
- Mutual-TLS metrics worked; a request missing its client certificate received a TLS certificate-required alert.
- Prometheus scraped federation successfully. `promtool` validated its config and all three alert rules.
- Grafana authenticated dashboard API returned the expected UID and eight panels.
  Visual rendering has not been inspected.
- The network-isolated privacy reference ran three rounds, reported noise/utility
  tradeoffs and explicitly kept its production privacy claim false.
- A real PostgreSQL custom-format dump was encrypted and restored into a fresh
  database. Two synthetic rows, primary key and quantity check constraint matched;
  the source rows remained intact.

Endpoint evidence: `outputs/acceptance-yufs0g60.json`.
Post-upgrade endpoint evidence: `outputs/acceptance-ql08940l.json`; all six checks passed.
Recovery evidence: `outputs/backups/drill-0j4yt0nw/report.json`.
Reports and secrets are ignored by Git; these paths describe this host only.
After dependency upgrades, all 30 federation checks passed and `pip check` found
no broken requirements. The updated container clients submitted another synthetic
round; server aggregation must still be checked independently of submission.

## Remaining external and production gates

- Member 2 implements business APIs, authorized approval and atomic inventory updates.
- Member 3 supplies agreed forecast/model contracts and eligible training data.
- The team activates CI from root `.github/workflows/`, outside the infra-only scope.
- Security scans must be reviewed. Initial scans found vulnerable dependencies and
  unfixed Debian findings. Compatible remediation and follow-up results are documented
  in [security scanning](security-scanning.md); there is no blanket clean-security claim.
- Real application data recovery, independently recoverable keys, off-host retention,
  object storage, alert delivery and production deployment remain separate acceptance work.
- The privacy prototype needs authenticated peer-key exchange, separate client isolation,
  durable accounting and an audit before use with real health data.

Local services are intentionally left running on loopback. Stop with all four
Compose files and `down` without `--volumes` to preserve database/model state.
