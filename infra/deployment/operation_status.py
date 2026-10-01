"""Atomic, non-sensitive scheduler results consumed by authenticated metrics."""
import json
import os
from pathlib import Path
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1] / 'outputs/operations'


def record(operation, success, directory=ROOT):
    if operation not in ('backup', 'restore') or type(success) is not bool:
        raise ValueError('Invalid operation result')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f'{operation}.json'
    previous = {}
    if target.is_file():
        try:
            previous = json.loads(target.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
    now = time.time()
    result = {'last_attempt': now, 'success': success,
              'last_success': now if success else previous.get('last_success', 0)}
    descriptor, name = tempfile.mkstemp(prefix=operation, dir=directory)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(result, stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)
