"""Load narrowly allowlisted secrets mounted by a host or external secret manager."""
import os
from pathlib import Path

NAMES = ('JWT_SECRET', 'JWT_REFRESH_SECRET', 'POSTGRES_PASSWORD', 'DATABASE_URL', 'REDIS_URL')


def inject(environment=None):
    environment = os.environ if environment is None else environment
    for name in NAMES:
        filename = environment.get(name+'_FILE')
        if not filename:
            continue
        if environment.get(name):
            raise ValueError(f'Configure only {name} or {name}_FILE')
        with Path(filename).open('rb') as source:
            raw = source.read(8193)
        if not raw.strip() or len(raw)>8192:
            raise ValueError(f'Invalid mounted secret: {name}')
        secret = raw.decode('utf-8').rstrip('\r\n')
        if any(character in secret for character in ('\x00','\r','\n')):
            raise ValueError(f'Invalid mounted secret format: {name}')
        environment[name] = secret
