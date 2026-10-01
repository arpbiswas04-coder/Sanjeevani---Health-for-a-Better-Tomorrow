"""Run on a provisioned Linux Docker host. Isolated release trees, persistent volumes.

Invoked over verified SSH by ssh_deploy.py. The operator owns shared/.env,
shared/federated-secrets and valid external TLS/ingress configuration.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
from urllib.request import urlopen
from urllib.parse import urlsplit

FILES = ['compose.yaml', 'compose.team.yaml', 'compose.monitoring.yaml', 'compose.grafana.yaml',
         'compose.observability.yaml', 'compose.alerts.yaml', 'compose.ingress.yaml', 'compose.production.yaml']


def deploy(root, sha, environment):
    root = Path(root).resolve()
    if environment not in ('staging', 'production') or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Invalid release identity')
    shared = root/'shared'
    env_file = shared/'.env'
    if env_file.stat().st_mode & 0o077:
        raise ValueError('Shared environment file must be owner-only')
    values = {}
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
    origin = values.get('PUBLIC_HTTPS_ORIGIN', '')
    url = urlsplit(origin)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError('Provision PUBLIC_HTTPS_ORIGIN as a valid HTTPS origin')
    for key in ('NGINX_TLS_DIRECTORY', 'NGINX_CONFIG'):
        if not Path(values.get(key, '')).is_absolute() or not Path(values[key]).exists():
            raise ValueError('Provision external TLS directory and rendered Nginx config')
    if values.get('CORS_ALLOWED_ORIGINS') is None or '*' in values['CORS_ALLOWED_ORIGINS']:
        raise ValueError('Explicit CORS allowlist required')
    if origin not in json.loads(values['CORS_ALLOWED_ORIGINS']):
        raise ValueError('CORS must include the deployed HTTPS origin')
    if not (shared/'federated-secrets/local-dev/manifest.json').is_file():
        raise ValueError('Provision service-specific federation and monitor identities first')
    for name in ('outputs', 'checkpoints'):
        if not (shared/name).is_dir():
            raise ValueError('Provision persistent outputs and checkpoints directories first')
    archive = root/'incoming'/f'{sha}.tar'
    release = root/'releases'/sha
    if release.exists():
        raise ValueError('Release directory already exists; never overwrite')
    release.mkdir(parents=True)
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if any(m.issym() or m.islnk() or not (m.isfile() or m.isdir()) for m in members):
            raise ValueError('Release must contain regular files/directories only')
        source.extractall(release, filter='data')
    infra = release/'infra'
    (infra/'federated/secrets').symlink_to(shared/'federated-secrets', target_is_directory=True)
    (infra/'federated/checkpoints').symlink_to(shared/'checkpoints', target_is_directory=True)
    (infra/'outputs').symlink_to(shared/'outputs', target_is_directory=True)
    (infra/'.env').symlink_to(env_file)
    pointer = root/'current-release'
    previous = pointer.read_text().strip() if pointer.exists() else None
    if previous and not re.fullmatch('[0-9a-f]{40}', previous):
        raise ValueError('Invalid prior release pointer')

    def apply(path, *, build):
        prefix = ['docker', 'compose', '--project-name', f'sanjeevani-{environment}',
                  '--env-file', str(env_file)]
        for filename in FILES:
            prefix += ['-f', str(path/'infra'/filename)]
        subprocess.run([*prefix, 'config', '--quiet'], check=True, timeout=60)
        subprocess.run([*prefix, 'up', '-d', '--build' if build else '--no-build',
                        '--wait', '--wait-timeout', '180'], check=True, timeout=1800)

    try:
        apply(release, build=True)
        with urlopen(origin+'/api/v1/ready', timeout=10) as response:
            if json.load(response).get('status') != 'ok':
                raise ValueError('Post-deployment health failed')
    except Exception:
        if previous:
            # Rebuild the prior reviewed revision: no database rollback/migrations.
            apply(root/'releases'/previous, build=True)
        raise
    temporary = root/'current-release.tmp'
    temporary.write_text(sha)
    os.replace(temporary, pointer)
    return {'deployed_sha': sha, 'environment': environment, 'health_verified': True,
            'previous_sha': previous, 'database_migrations_applied': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    parser.add_argument('sha')
    parser.add_argument('environment', choices=['staging', 'production'])
    args = parser.parse_args()
    print(json.dumps(deploy(args.root, args.sha, args.environment)))
