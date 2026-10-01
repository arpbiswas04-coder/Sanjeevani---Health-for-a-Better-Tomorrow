# Encrypted federation backup and recovery

`python -m federated.backup` backs up validated coordinator checkpoint state using
Fernet authenticated encryption. It verifies the checkpoint before encryption,
and verifies decryption and coordinator schema before restoring. It never backs
up raw training data, node signing keys, TLS private keys or pending updates.

## Key setup

Run from `infra/` using the existing federation environment. After provisioning
the restricted `local-dev` credential directory, create a separate backup key once:

```powershell
.\.venv-federated\Scripts\python.exe -c "from cryptography.fernet import Fernet; from pathlib import Path; p=Path('federated/secrets/local-dev/backup.key'); f=p.open('xb'); f.write(Fernet.generate_key()); f.close()"
```

The key is written without being printed. Existing files are refused. On Windows
it inherits the provisioned directory's restrictions; on Linux restrict the file
to mode 0600 as well. Use a separate securely stored copy of this key for disaster
recovery. Losing it makes the backups unreadable; storing only the key and backups
on the same disk does not protect against disk loss. No persistent key was created
during implementation validation.

## Back up and verify

Choose an existing completed checkpoint and a unique output name:

```powershell
.\.venv-federated\Scripts\python.exe -m federated.backup backup --source federated/checkpoints/local-dev.json --output federated/backups/round-backup-001.enc --key-file federated/secrets/local-dev/backup.key
.\.venv-federated\Scripts\python.exe -m federated.backup verify --source federated/backups/round-backup-001.enc --key-file federated/secrets/local-dev/backup.key
```

The backup contains model state, round/version metadata and recorded node metadata.
Output is bounded to 2 MiB. Verification decrypts in memory and reports only status,
backup time and model version. Fernet tokens reveal their creation timestamp; the
checkpoint contents are encrypted. This uses the
[cryptography Fernet API](https://cryptography.io/en/latest/fernet/).

Atomic checkpoint replacement means a concurrent backup normally reads one complete
saved checkpoint, not pending contributions. It may be the preceding round. For a
specific recovery point, stop admission after the required saved round first.

For the Docker stack, export the named-volume checkpoint into an unused ignored
host path first. `docker compose cp federation-server:/app/infra/federated/checkpoints/compose.json federated/checkpoints/compose-export.json`
copies plaintext; ensure the destination does not already contain work you need.
Then back up that exported file. Docker volume export has not been verified here.

## Restore to a new checkpoint

```powershell
.\.venv-federated\Scripts\python.exe -m federated.backup restore --source federated/backups/round-backup-001.enc --output federated/checkpoints/recovered-001.json --key-file federated/secrets/local-dev/backup.key
```

Restore creates a new plaintext checkpoint, reloads the staged file to confirm
state equality, and publishes it without replacing an existing file. Stop the
coordinator before deliberately switching it to this recovered checkpoint; use
the HTTPS server's `--checkpoint` argument. The local/Compose launchers' fixed
checkpoint paths are not changed automatically. Node credentials must still match
the recovered node registry. Restart generates a fresh challenge and clients must
fetch the new round state; old packets cannot be replayed through admission.

Both backup and restore require output under `infra/`. They use a temporary file
and an exclusive hard link on the same filesystem to publish without overwriting.
NTFS/local recovery was checked; filesystems without hard-link support fail safely.
Power-loss durability of directory entries is not guaranteed. Restore necessarily
writes plaintext to its staging directory and final checkpoint; restrict the
destination directory to the service user. A crash may leave staging files for
manual inspection. No automatic cleanup of old backups or retention deletion occurs.

## Scope and validation

One focused recovery check passed: exact state recovery, wrong-key rejection,
tamper rejection, and refusal to overwrite either backups or checkpoints. Temporary
fixtures were removed. No training, server or broad suite ran.

```powershell
.\.venv-federated\Scripts\python.exe -m unittest federated.tests.test_backup -v
```

This is an on-demand local recovery tool. Scheduling, off-host copies, key rotation,
retention policy, operational restore drills, PostgreSQL backups and object-storage
recovery are still pending. Do not treat a federation checkpoint backup as a backup
of the entire Sanjeevani application.
