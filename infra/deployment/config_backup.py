"""Encrypt explicitly selected non-secret infra configuration; verify fresh restore."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import tempfile
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
# Closed selection: never recurse into secrets, environment files or volumes.
FILES = ('compose.yaml', 'compose.team.yaml', 'compose.monitoring.yaml',
         'compose.grafana.yaml', 'compose.observability.yaml', 'compose.alerts.yaml',
         'monitoring/alertmanager.local.yml', 'monitoring/prometheus/local-alerts.yml',
         'monitoring/prometheus/team.yml', 'monitoring/prometheus/application-alerts.yml',
         'monitoring/prometheus/federation-alerts.yml',
         'monitoring/grafana/dashboards/application.json',
         'monitoring/grafana/dashboards/federation.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file', type=Path, default=ROOT / 'federated/secrets/local-dev/backup.key')
    args = parser.parse_args()
    key_path = args.key_file.resolve()
    if not key_path.is_relative_to(ROOT / 'federated/secrets'):
        raise ValueError('Key must remain in the restricted secrets directory')
    cipher = Fernet(key_path.read_bytes().strip())
    content = {}
    for name in FILES:
        source = ROOT / name
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
            raise ValueError('Configuration cannot be a link outside infra')
        if source.stat().st_size > 1024 * 1024:
            raise ValueError('Configuration exceeds limit')
        content[name] = base64.b64encode(source.read_bytes()).decode('ascii')
    encrypted = cipher.encrypt(json.dumps(content).encode('utf-8'))
    output = ROOT / 'outputs/backups'
    output.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='config-', dir=output))
    archive = directory / 'config.enc'
    with archive.open('xb') as stream:
        stream.write(encrypted)
    recovered = json.loads(cipher.decrypt(archive.read_bytes()))
    if set(recovered) != set(FILES):
        raise ValueError('Restore member mismatch')
    restore = directory / 'restored'
    restore.mkdir()
    for name in FILES:
        target = restore / name
        target.parent.mkdir(parents=True, exist_ok=True)
        value = base64.b64decode(recovered[name], validate=True)
        with target.open('xb') as stream:
            stream.write(value)
        if target.read_bytes() != base64.b64decode(content[name]):
            raise ValueError('Restored bytes differ')
    report = {'status': 'config_backup_created', 'sha256': hashlib.sha256(encrypted).hexdigest(),
              'restore_verified': True, 'files': list(FILES), 'off_host_copy': 'not_configured',
              'scope': 'Explicit non-secret infra configuration only; excludes environment, keys and application data'}
    (directory / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'evidence_directory': str(directory), **report}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError):
        print('config_backup_failed: verify configuration and key access; no existing files changed')
        raise SystemExit(2)
