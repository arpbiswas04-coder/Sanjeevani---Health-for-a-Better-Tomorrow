"""Generate dev-only Compose credentials without printing or replacing secrets."""
import csv
import os
from pathlib import Path
import secrets
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    # Exclusive placeholder is empty until permissions have been restricted.
    with target.open("x", encoding="utf-8"):
        pass
    if os.name == "nt":
        output = subprocess.run(["whoami.exe", "/user", "/fo", "csv", "/nh"], check=True, capture_output=True, text=True)
        sid = next(csv.reader(output.stdout.splitlines()))[1]
        if not sid.startswith("S-1-"): raise ValueError("Unknown Windows SID")
        subprocess.run(["icacls.exe", str(target), "/inheritance:r", "/grant:r", f"*{sid}:F"], check=True, capture_output=True)
    else:
        target.chmod(0o600)
    values = {key: secrets.token_hex(32) for key in ("MEMBER4_DB_PASSWORD", "MEMBER4_JWT_SECRET", "MEMBER4_JWT_REFRESH_SECRET")}
    target.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
    print("Created restricted infra/.env; keep it private and do not regenerate for an existing database volume.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        print("Environment preparation failed; check existing infra/.env and permissions. No secret values printed.")
        raise SystemExit(2)
