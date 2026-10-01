"""Explicit SSH deployment with pinned host keys; never invoked on a PR event."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def validate(host, user, root, sha, environment):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}', host):
        raise ValueError('Invalid host')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', user):
        raise ValueError('Invalid user')
    if not re.fullmatch(r'/[A-Za-z0-9_/-]+', root) or '..' in root or root in ('/', '/srv', '/opt', '/home'):
        raise ValueError('Use a dedicated absolute deployment path')
    if not re.fullmatch(r'[0-9a-f]{40}', sha) or environment not in ('staging', 'production'):
        raise ValueError('Invalid revision/environment')


def main():
    if os.environ.get('DEPLOY_PROVIDER') != 'ssh-compose':
        raise ValueError('DEPLOY_PROVIDER=ssh-compose must be selected explicitly')
    host, user, root, sha, environment = [os.environ[k] for k in (
        'DEPLOY_HOST', 'DEPLOY_USER', 'DEPLOY_PATH', 'DEPLOY_SHA', 'DEPLOY_ENVIRONMENT')]
    validate(host, user, root, sha, environment)
    with tempfile.TemporaryDirectory(prefix='member4-deploy-') as directory:
        folder = Path(directory)
        key, known, archive = folder/'key', folder/'known_hosts', folder/'release.tar'
        for path, value in ((key, os.environ['DEPLOY_SSH_KEY']), (known, os.environ['DEPLOY_KNOWN_HOSTS'])):
            if not value.strip():
                raise ValueError('Empty SSH credentials or known-host pins')
            path.write_text(value+'\n')
            path.chmod(0o600)
        options = ['-i', str(key), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
                   '-o', 'StrictHostKeyChecking=yes', '-o', f'UserKnownHostsFile={known}', '-o', 'ConnectTimeout=10']
        destination = f'{user}@{host}'
        subprocess.run(['git', 'archive', '--format=tar', '-o', str(archive), sha], check=True, timeout=120)
        subprocess.run(['ssh', *options, destination, f'mkdir -p {root}/incoming'], check=True, timeout=30)
        subprocess.run(['scp', *options, str(archive), f'{destination}:{root}/incoming/{sha}.tar'], check=True, timeout=300)
        script = Path(__file__).with_name('remote_release.py').read_bytes()
        subprocess.run(['ssh', *options, destination, f'python3 - {root} {sha} {environment}'],
                       input=script, check=True, timeout=2100)


if __name__ == '__main__':
    main()
