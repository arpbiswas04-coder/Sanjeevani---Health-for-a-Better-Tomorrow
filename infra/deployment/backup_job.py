"""One scheduler-friendly local encrypted backup; retention is a reviewable plan."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
try:
    from .operation_status import record
except ImportError:
    from operation_status import record

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="sanjeevani")
    parser.add_argument("--keep", type=int, default=7, help="Number of successful local job archives to retain in the proposed plan")
    args = parser.parse_args()
    if not 1 <= args.keep <= 365: raise ValueError("Retention must be 1..365 archives")
    root = ROOT / "outputs/backups"
    root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="scheduled-", dir=root))
    archive = directory / "postgres.enc"
    try:
        result = subprocess.run([sys.executable, str(ROOT / "security/postgres_recovery.py"), "backup", "--compose",
                                 "--database", args.database, "--user", "sanjeevani", "--key-file",
                                 str(ROOT / "federated/secrets/local-dev/backup.key"), "--file", str(archive)],
                                capture_output=True, text=True, timeout=240)
    except (OSError, subprocess.SubprocessError):
        (directory / "failure.json").write_text(json.dumps({"status": "backup_failed",
            "reason": "execution_failed_or_timed_out", "created_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
        return 2
    if result.returncode:
        (directory / "failure.json").write_text(json.dumps({"status": "backup_failed",
            "reason": "backup_command_failed", "exit_code": result.returncode,
            "created_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
        print(json.dumps({"status":"backup_failed", "job_directory":str(directory)}))
        return 2
    report = {"status":"backup_created", "created_at":datetime.now(timezone.utc).isoformat(),
              "database":args.database, "encrypted_archive":str(archive),
              "sha256":hashlib.sha256(archive.read_bytes()).hexdigest(), "restore_verified":False,
              "off_host_copy":"not_configured", "retention_keep":args.keep}
    (directory / "manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    # Plan only: no deletion and no access to unrelated directories or archives.
    candidates = sorted((p for p in root.glob('scheduled-*/manifest.json') if p.is_file() and not p.is_symlink()),
                        key=lambda p:p.stat().st_mtime, reverse=True)
    report["retention_review_candidates"]=[str(p.parent) for p in candidates[args.keep:]]
    (directory / "retention-plan.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0


if __name__ == "__main__":
    try:
        result = main()
        record("backup", result == 0)
        raise SystemExit(result)
    except (OSError, ValueError, subprocess.SubprocessError):
        record("backup", False)
        print('backup_job_failed: check Docker, key and local database; existing archives preserved')
        raise SystemExit(2)
