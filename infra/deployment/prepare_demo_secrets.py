"""Create missing local Grafana/backup secrets inside an existing restricted bundle."""
from pathlib import Path
import os
import secrets


def main():
    from cryptography.fernet import Fernet
    directory = Path(__file__).resolve().parents[1] / "federated/secrets/local-dev"
    if not (directory / "manifest.json").is_file():
        raise ValueError("Provision the local-dev credential bundle first")
    for name, generate in (("grafana-admin-password", lambda: secrets.token_urlsafe(32).encode()),
                           ("backup.key", Fernet.generate_key),
                           ("metrics-token", lambda: secrets.token_urlsafe(32).encode())):
        target = directory / name
        if target.exists():
            continue
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(generate())
            stream.flush()
            os.fsync(stream.fileno())
    print("Local Grafana and backup secrets prepared; existing files preserved; values not printed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ImportError):
        print("Secret preparation failed; check the restricted bundle and federation environment.")
        raise SystemExit(2)
