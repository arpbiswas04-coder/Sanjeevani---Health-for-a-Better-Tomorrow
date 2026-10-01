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

## Configuration backup and off-host copy interface

`deployment/config_backup.py` encrypts a closed list of ten actual Compose,
Prometheus and Grafana files using the separately stored backup key. It decrypts
the archive into a new directory and verifies every restored file byte-for-byte.
The local drill passed in `outputs/backups/config-g928yr1d/manifest.json`.
It excludes environment files, secrets and application data. Object storage is
not present in this stack; object-store backup therefore awaits an actual service.

`deployment/archive_copy.py --archive <absolute-path-to-.enc> --destination <mounted-directory>`
is an explicit operator action. It requires an existing destination outside infra,
validates the source manifest checksum, creates a unique destination, copies only
the encrypted archive, reads it back and records a minimal checksum receipt.
Missing configuration or checksum mismatch fails. It never copies keys, overwrites,
prunes or mounts a network share. A mounted path is not proof of off-host durability;
the operator must provision/verify that storage and perform a separate restore.
No real off-host copy has been executed. Two isolated local checks verified
copy/read-back and tamper/missing-destination rejection.

Backup command failures/timeouts now leave a sanitized `failure.json` inside the
new job directory and return nonzero, without recording raw stderr or credentials.

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

Six Prometheus rules are loaded and validated with observability. External delivery requires a
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

The executable local startup is `deployment/start-local.ps1 -Observability -Grafana`.
The CI template remains in `infra/ci-cd/`; activation needs a root workflow change
by the team. Cloud deployment requires a selected target, secrets, migration plan,
rollback plan and resolved security gates. These are not satisfied by local health checks.

## October 1 local-only release update

Local alert firing/resolution and encrypted backup copy/decryption are verified.
The new Alertmanager gRPC finding was fixed and its HIGH/CRITICAL rescan passed.
Existing backend/federation security blockers remain. Hosted CI stays inactive
under the explicitly reconfirmed infra-only restriction. Cloud/off-host services
were excluded by the selected local-only target. See local-release-status.md.
