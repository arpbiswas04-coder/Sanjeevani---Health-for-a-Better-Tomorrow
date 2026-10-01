# Local PostgreSQL backup and restore drill

`security/postgres_recovery.py` supplies an encrypted custom-format dump and a
restore into a **new, randomly named** `member4_restore_*` database. It never
overwrites or drops the source database. Restored databases are left for inspection.

Prerequisites: a local PostgreSQL server, matching-version PostgreSQL client tools
(`pg_dump`, `createdb`, `pg_restore`) on PATH, the federation Python environment,
and a Fernet key in the restricted `federated/secrets/` directory. Reuse the key
creation procedure in [federation recovery](federated-backup.md), preferably with a
dedicated database backup key. Supply database credentials using a restricted
`PGPASSFILE`; no password is placed in command-line arguments and prompting is
disabled. The restore user needs database creation permissions.

From `infra/`:

```powershell
.\.venv-federated\Scripts\python.exe security/postgres_recovery.py backup --database sanjeevani --user sanjeevani --key-file federated/secrets/local-dev/backup.key --file outputs/backups/postgres-001.enc
.\.venv-federated\Scripts\python.exe security/postgres_recovery.py restore-drill --user sanjeevani --key-file federated/secrets/local-dev/backup.key --file outputs/backups/postgres-001.enc
```

For the local team Compose stack, add `--compose` to either command. The helper
uses matching-version tools inside `app-postgres`, connects over its local trusted
socket, and streams the dump through Docker stdin/stdout. Host PostgreSQL tools
and host `PGPASSFILE` are unnecessary for this mode; protect access to Docker.
Never enable trusted connections on externally exposed database interfaces.
`deployment/prepare_demo_secrets.py` creates a missing dedicated backup key.

Run a repeatable isolated synthetic drill with:

```powershell
.\.venv-federated\Scripts\python.exe deployment/recovery_drill.py
```

The tool always connects to 127.0.0.1, with configurable `--port`. Dumps must be at
most 64 MiB for this small demo utility. Encryption uses bounded whole-file Fernet;
larger deployments need a streaming backup product. Dump creation can temporarily
use more disk before the size check. Plaintext staging lives beside the restricted
key and is removed on normal exit; inspect for leftovers after a crash. Never use
a public/shared directory for the key or `PGPASSFILE`.

Only restore trusted backups: PostgreSQL restores execute database definitions.
The drill omits original ownership/ACLs and requires `pg_restore` success in one
transaction. It does not prove application correctness: check expected table/row
counts, constraints, migrations, permissions and application startup in the new
database. Roles, object-store files, credentials and deployment configuration are
not included. Schedule off-host copies and independent key recovery separately.

A real container-based synthetic drill passed on September 30, including restored
row values and primary-key/check constraints; report location is in the
[local acceptance record](local-demo-acceptance.md). This validates the helper on
PostgreSQL 16. It does not validate missing application tables, migrations, roles,
object storage or off-host disaster recovery.
