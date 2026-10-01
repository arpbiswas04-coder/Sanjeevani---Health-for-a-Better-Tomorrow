# PostgreSQL backup contract and manual runbook

The backend records infrastructure-reported backup metadata; it does not execute
pg_dump, delete backup objects or restore databases. Member 4 owns those operations.
`GET /api/v1/admin/backups/status` reports recent completion, retention configuration
and whether infrastructure reported a verification time. It does not prove that an
artifact exists, matches a checksum or can be restored.

## Infrastructure configuration

- Set BACKUP_STORAGE_NAME to a non-secret storage label.
- Set BACKUP_RETENTION_DAYS and BACKUP_MAX_AGE_HOURS to the agreed policy.
- Keep storage credentials and PostgreSQL credentials in the infrastructure secret
  manager or protected PostgreSQL service/password files. Never commit those files.
- Schedule backups using the infrastructure scheduler, outside application request
  workers. Use encrypted storage and transport and a dedicated least-privileged role.
- Preserve audit trails of backup completion, checksum verification and retention
  actions. A failed backup must never be reported as completed.

A typical manually configured command is:

```text
pg_dump --dbname=service=sanjeevani_backup --format=custom --file=BACKUP_ARTIFACT
```

Here `sanjeevani_backup` is an operator-configured libpq service name and
BACKUP_ARTIFACT is an operator-chosen file path. No credentials belong in the
command line. The service/role must be able to read the required tables and
extensions. Version pg_dump consistently with the PostgreSQL server.

After the command succeeds, calculate an actual SHA-256 checksum and actual file
size, upload/verify the encrypted artifact, and submit metadata to
`POST /api/v1/admin/backups` using an authorized infrastructure account. Record an
artifact key, not a signed URL or credential-bearing storage location. The backend
validates status, checksum shape, size and timestamp ordering, but relies on the
trusted infrastructure caller for their truth.

## Retention and verification

Apply retention through the storage provider after confirming newer verified copies
exist. This backend exposes the desired retention period but never deletes backup
objects automatically. Test recovery regularly into a newly provisioned disposable
database, isolated from production traffic and credentials. Verify schema, extensions,
record counts, representative queries and operational invariants before recording a
verified_at timestamp. Restore exercises require an explicit operator action; no
backend endpoint performs or authorizes a destructive restore.

Manual validation should include a fresh PostgreSQL/PostGIS test deployment, Alembic
head checks and the opt-in tests documented in README.md. Monitor backup age and
failed attempts independently from API availability. An HTTP 200 from the API is
not evidence of a usable backup.
