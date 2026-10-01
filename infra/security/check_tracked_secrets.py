"""Fail on tracked private runtime files or recognizable secret material; redact values."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = [re.compile(rb'^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
            re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),
            re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{36,255}\b')]


def violations(path):
    name = path.as_posix()
    if path.name == '.env' or (path.name.startswith('.env.') and path.name != '.env.example'):
        return True
    if name.startswith(('infra/federated/secrets/', 'infra/outputs/', 'infra/federated/checkpoints/')):
        return True
    source = ROOT / path
    if source.is_symlink():
        return False
    with source.open('rb') as stream:
        return any(pattern.search(line) for line in stream for pattern in PATTERNS)


def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    bad = [name for name in tracked if name and violations(Path(name))]
    for name in bad:
        print('Tracked secret policy violation: ' + name)
    print(f'Tracked secret policy: {len(bad)} violation(s); values never printed')
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())
