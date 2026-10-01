"""Explicit copy of one encrypted backup to an operator-mounted destination.

No network credentials, mounts, bucket creation, overwrite or pruning. A mounted
destination is not proof of off-host durability; the operator owns that boundary.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 96 * 1024 * 1024


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def copy_archive(archive, destination, *, local_demo=False):
    archive, destination = Path(archive).resolve(), Path(destination).resolve()
    if not archive.is_relative_to(ROOT / 'outputs/backups') or archive.suffix != '.enc':
        raise ValueError('Source must be an encrypted backup under infra/outputs/backups')
    if not archive.is_file() or not 1 <= archive.stat().st_size <= LIMIT:
        raise ValueError('Missing or oversized archive')
    manifest = json.loads(archive.with_name('manifest.json').read_text(encoding='utf-8'))
    expected = manifest.get('sha256')
    if expected != digest(archive):
        raise ValueError('Source checksum does not match manifest')
    if local_demo:
        if not destination.is_relative_to(ROOT / 'outputs/backup-copy-demo'):
            raise ValueError('Local demonstration destination must be under outputs/backup-copy-demo')
    elif destination.is_relative_to(ROOT):
        raise ValueError('Real copy destination must be outside infra')
    if not destination.is_dir():
        raise ValueError('Supply an existing operator-mounted destination outside infra')
    # Unique subdirectory: never overwrite an existing backup. Failed copies stay
    # without a verification receipt and must not be counted as successful.
    job = destination / ('sanjeevani-' + uuid.uuid4().hex)
    job.mkdir()
    target = job / 'backup.enc'
    with archive.open('rb') as source, target.open('xb') as output:
        shutil.copyfileobj(source, output, length=1024 * 1024)
    if digest(target) != expected:
        raise ValueError('Destination read-back checksum mismatch')
    receipt = {'sha256': expected, 'readback_verified': True,
               'off_host_durability_verified': False, 'restore_verified': False,
               'archive': 'backup.enc'}
    with (job / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    return job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--local-demo', action='store_true', help='Allow only outputs/backup-copy-demo as a same-host destination')
    args = parser.parse_args()
    try:
        target = copy_archive(args.archive, args.destination, local_demo=args.local_demo)
    except (OSError, ValueError, TypeError):
        print('archive_copy_failed: source, manifest or destination invalid; no verified copy recorded')
        return 2
    print(json.dumps({'status': 'copy_readback_verified', 'destination': str(target)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
