# Remaining operational integrations

## Scheduled backup entry point

From `infra/`, run with the federation environment:

```powershell
.\.venv-federated\Scripts\python.exe deployment/backup_job.py --database sanjeevani --keep 7
```

Each invocation makes a new encrypted PostgreSQL backup, SHA256 manifest and
retention review plan under ignored `outputs/backups/scheduled-*`. It returns
nonzero on failure, prints no secrets, preserves existing backups and never drops
a database. A backup is not marked restore-verified just because dumping succeeded.
Use `deployment/recovery_drill.py` for the synthetic drill, or the recovery guide
for an actual application restore into a new database and application-level checks.

A team operator can register this command in Windows Task Scheduler with the
absolute Python/script paths, the infra working directory, and a user account
that can access Docker and the restricted backup key. Docker must be running.
No task has been registered; choose schedule, operator and failure notification
before activation. `--keep` controls the retention plan, not destructive pruning.

## Off-host storage contract (not provisioned)

Upload only the encrypted archive and manifest to a team-selected private bucket
with encryption, versioning, access logging and a lifecycle policy. Use a workload
identity or secret-manager credential; do not put access keys in this repository.
Verify the remote checksum before recording success or applying retention.
Keep the Fernet key separately in recoverable key custody; storing it beside the
remote archive defeats separation. Suggested metadata: job timestamp, source DB,
archive digest, remote object/version ID, verification time and restore-drill ID.
Destination, account, RPO/RTO, retention period and key custodian are not supplied.
No off-host upload, object-store backup or deletion has been executed.

## Alert delivery contract (not activated)

Three Prometheus rules are loaded and validated. External delivery requires a
team-controlled Alertmanager/receiver and a verified destination. Store receiver
tokens under restricted `federated/secrets/` or a secret manager. Proposed routing:
critical `FederationScrapeUnavailable` to the on-call receiver; warning
`FederationRoundStalled` and `FederationInsufficientParticipants` to the engineering
receiver. Group by alertname/instance, repeat at most every four hours and send
resolved notifications. Validate with a synthetic alert before claiming delivery.
Do not publish metrics, node credentials or health data in alert payloads.
Without receiver details, no external notifications are sent and delivery remains
blocked by the team operator. An inactive config example is supplied separately.

## Deployment and CI

The executable local startup is `deployment/start-local.ps1 -Team -Monitoring -Grafana`.
The CI template remains in `infra/ci-cd/`; activation needs a root workflow change
by the team. Cloud deployment requires a selected target, secrets, migration plan,
rollback plan and resolved security gates. These are not satisfied by local health checks.
