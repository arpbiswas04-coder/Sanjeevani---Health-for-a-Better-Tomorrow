"""Local PostgreSQL encrypted backup and restore into a new drill database only."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 64 * 1024 * 1024  # Bounded in-memory encryption: small local demo databases.


def invoke(command, *, output=None):
    subprocess.run(command, stdout=output if output is not None else subprocess.DEVNULL,
                   stderr=subprocess.PIPE, check=True, timeout=180)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "restore-drill"))
    parser.add_argument("--database", help="Source database for backup only")
    parser.add_argument("--user", required=True)
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--file", type=Path, required=True, help="Encrypted output/input")
    args = parser.parse_args()
    try:
        from cryptography.fernet import Fernet
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", args.user): raise ValueError("Invalid user")
        if not 1 <= args.port <= 65535: raise ValueError("Invalid port")
        tools = ("pg_dump",) if args.action == "backup" else ("createdb", "pg_restore")
        if any(shutil.which(tool) is None for tool in tools): raise ValueError("PostgreSQL client tools missing")
        with args.key_file.open("rb") as stream: key = stream.read(129).strip()
        if len(key) != 44: raise ValueError("Invalid key")
        cipher = Fernet(key)
        # Stage beside the key: use the existing restricted credential directory.
        staging_root = args.key_file.resolve().parent
        if not staging_root.is_relative_to(ROOT / "federated/secrets"):
            raise ValueError("Key/staging directory must be under infra/federated/secrets")
        connection = ["--host", "127.0.0.1", "--port", str(args.port), "--username", args.user, "--no-password"]
        with tempfile.TemporaryDirectory(prefix=".pg-drill-", dir=staging_root) as directory:
            dump = Path(directory) / "database.dump"
            if args.action == "backup":
                if not args.database or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", args.database): raise ValueError("Invalid database")
                target = args.file.absolute()
                if not target.resolve().is_relative_to(ROOT) or target.exists() or target.is_symlink():
                    raise ValueError("Output must be a new file inside infra")
                with dump.open("xb") as stream:
                    invoke(["pg_dump", *connection, "--format=custom", "--dbname", args.database], output=stream)
                if dump.stat().st_size > LIMIT: raise ValueError("Dump exceeds 64 MiB demo limit")
                encrypted = cipher.encrypt(dump.read_bytes())
                target.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive create prevents overwriting a backup. Incomplete files
                # after interruption fail Fernet authentication and must not be trusted.
                with target.open("xb") as stream:
                    stream.write(encrypted)
                    stream.flush()
                    os.fsync(stream.fileno())
                print(json.dumps({"status": "backup_created", "path": str(target), "restore_verified": False}))
            else:
                if args.database is not None: raise ValueError("Restore chooses a fresh database name")
                with args.file.open("rb") as stream: encrypted = stream.read(2 * LIMIT + 1)
                if len(encrypted) > 2 * LIMIT: raise ValueError("Backup exceeds size limit")
                content = cipher.decrypt(encrypted)
                if len(content) > LIMIT or not content.startswith(b"PGDMP"): raise ValueError("Invalid PostgreSQL custom dump")
                dump.write_bytes(content)
                invoke(["pg_restore", "--list", str(dump)])
                database = "member4_restore_" + secrets.token_hex(8)
                invoke(["createdb", *connection, "--template=template0", database])
                try:
                    invoke(["pg_restore", *connection, "--exit-on-error", "--single-transaction", "--no-owner",
                            "--no-privileges", "--dbname", database, str(dump)])
                except (OSError, subprocess.SubprocessError):
                    print(json.dumps({"status": "restore_failed", "inspection_database": database}))
                    return 2
                print(json.dumps({"status": "restored_for_inspection", "database": database,
                                  "application_data_validation": "pending"}))
        return 0
    except (OSError, ValueError, ImportError, subprocess.SubprocessError):
        print("postgres_recovery_failed: check tools, credentials, local database, key and file; no source database is overwritten")
        return 2
    except Exception as exc:
        # InvalidToken has no helpful public details; do not echo decrypted data.
        from cryptography.fernet import InvalidToken
        if not isinstance(exc, InvalidToken): raise
        print("postgres_recovery_failed: backup authentication failed")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
