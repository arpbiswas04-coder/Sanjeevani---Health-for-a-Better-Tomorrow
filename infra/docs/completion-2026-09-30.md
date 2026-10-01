# Latest completion evidence

All edits are within infra. Existing credentials, database/model volumes and
privacy accounting were preserved. No push, schedule, external upload or workflow
activation was performed.

Completed in this pass:

- Protected backend metrics, bounded dependency probes, optimizer timing and
  nine-panel application dashboard are running in the local Docker stack.
- Startup helper includes the observability overlay; ten endpoint checks pass
  after the final image rebuild (`outputs/acceptance-dsxvfzyi.json`).
- Promtool validates both rule files (six rules). Backend runs as UID 1000 with
  read-only root, dropped capabilities and no-new-privileges.
- Ten synthetic demos passed (`outputs/delivery-qlgyb6ht`).
- Encrypted configuration archive restored ten selected files byte-for-byte
  (`outputs/backups/config-g928yr1d/manifest.json`).
- Explicit mounted-destination copy verifies source and destination checksums.
  Missing destination and changed source fail. No actual off-host copy occurred.
- Backup failure reports are sanitized and persistent. Retention remains a plan.
- CI template now covers available frontend build/typecheck, Python static
  errors, backend/AI scaffold tests, monitoring checks and three image scans.
  Five edited YAML files parsed; hosted CI has not run.
- Backend image findings reduced from 52 to 44 by removing unused curl/client
  development packages. Remaining entries have no listed fix. Federation still
  has its separate 47 recorded findings. Neither scan is clean.

| Remaining gate | Owner | Required next action |
| --- | --- | --- |
| Real inventory, staff, fleet, RBAC and approved transfers | Member 2 | Implement authorized APIs and atomic approval/application against agreed contracts |
| Real forecasts/risk/models and observed prediction metrics | Member 3 | Supply versioned artifacts/data and implement inference; current tests check placeholders |
| Active frontend lint/tests and clinical/model checks | Members 1/3 | Add actual test commands/acceptance criteria; existing build/placeholder checks are insufficient |
| Hosted CI, branch protection and deployments | Team maintainer | Authorize root workflow activation, execute checks and supply deployment environment |
| Vulnerability remediation | Member 4/upstream maintainers | Review supported base/package fixes; no suppressed findings or production exception |
| Real-data privacy and BRICS participation | Team/partner operators | Authenticated peer keys, isolation, security review, partner data/model agreements |
| Off-host storage, independent keys, schedules and alert receiver | Operator | Supply/authorize destination, retention/RPO/RTO/key custody and verify delivery/recovery |
| Visual dashboard inspection | Operator/permitted browser tooling | Inspect rendering when URL safety validation permits; API success alone is insufficient |

Start from infra with `deployment/start-local.ps1 -Observability -Grafana`.
The stack remains running on loopback. See application-monitoring.md,
operations-completion.md, deployment-handoff.md and backend-security-findings.md.
