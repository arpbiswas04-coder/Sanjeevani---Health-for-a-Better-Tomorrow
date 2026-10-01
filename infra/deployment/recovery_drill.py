"""Exercise encrypted PostgreSQL recovery on an isolated synthetic demo database."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    docker = shutil.which("docker")
    if not docker:
        candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/DockerDesktop/resources/bin/docker.exe"
        if candidate.is_file():
            docker = str(candidate)
    if not docker:
        raise ValueError("Docker missing")
    environment = dict(os.environ)
    environment["PATH"] = str(Path(docker).parent) + os.pathsep + environment.get("PATH", "")
    prefix = [docker, "compose", "--project-directory", str(ROOT), "-f", str(ROOT / "compose.yaml"),
              "-f", str(ROOT / "compose.team.yaml"), "exec", "-T", "app-postgres"]

    def execute(command):
        return subprocess.run(command, check=True, capture_output=True, text=True, env=environment, timeout=180).stdout

    source = "member4_drill_" + secrets.token_hex(8)
    execute([*prefix, "createdb", "--username", "sanjeevani", "--no-password", "--template=template0", source])

    def sql(database, statement):
        return execute([*prefix, "psql", "--username", "sanjeevani", "--no-password", "--dbname", database,
                        "--no-align", "--tuples-only", "--set", "ON_ERROR_STOP=1", "--command", statement]).strip()

    sql(source, "CREATE TABLE recovery_probe(id integer PRIMARY KEY,label text NOT NULL,quantity integer CHECK(quantity>=0)); "
                "INSERT INTO recovery_probe VALUES (1,'synthetic-med-a',12),(2,'synthetic-med-b',0);")
    output = ROOT / "outputs/backups"
    output.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="drill-", dir=output))
    archive = directory / "postgres.enc"
    common = [sys.executable, str(ROOT / "security/postgres_recovery.py")]
    options = ["--compose", "--user", "sanjeevani", "--key-file", str(ROOT / "federated/secrets/local-dev/backup.key"),
               "--file", str(archive)]
    execute([*common, "backup", "--database", source, *options])
    restored = json.loads(execute([*common, "restore-drill", *options]))["database"]
    if not restored.startswith("member4_restore_") or restored == source:
        raise ValueError("Unsafe restore result")
    query = "SELECT json_agg(json_build_array(id,label,quantity) ORDER BY id) FROM recovery_probe;"
    expected = [[1, "synthetic-med-a", 12], [2, "synthetic-med-b", 0]]
    source_matches = json.loads(sql(source, query)) == expected
    restored_matches = json.loads(sql(restored, query)) == expected
    constraints = int(sql(restored, "SELECT count(*) FROM pg_constraint WHERE conrelid='recovery_probe'::regclass AND contype IN ('p','c');")) == 2
    passed = source_matches and restored_matches and constraints
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "passed": passed,
              "source_database": source, "restored_database": restored,
              "encrypted_backup": str(archive), "source_rows_unchanged": source_matches,
              "restored_rows_match": restored_matches, "primary_key_and_check_constraint_restored": constraints,
              "scope": "Real PostgreSQL custom dump/encryption/restore with synthetic rows; application database recovery remains separate"}
    (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        print("recovery_drill_failed: check Docker, PostgreSQL and prepared secrets; no source databases dropped")
        raise SystemExit(2)
