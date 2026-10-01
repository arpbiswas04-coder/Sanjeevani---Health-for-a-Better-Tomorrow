"""Explicit archive upload/download/list/retention planning; no automatic cleanup."""
import argparse
import json
from pathlib import Path
import sys
from deployment.backup_storage import configured_storage, LIMIT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['upload', 'download', 'list', 'retention-plan'])
    parser.add_argument('--file', type=Path)
    parser.add_argument('--key')
    parser.add_argument('--sha256')
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()
    try:
        storage = configured_storage()
        if args.action == 'upload':
            if args.file is None or args.file.suffix != '.enc' or not args.key:
                raise ValueError('Encrypted file/key required')
            with args.file.open('rb') as stream:
                raw = stream.read(LIMIT + 1)
            manifest = json.loads(args.file.with_name('manifest.json').read_text(encoding='utf-8'))
            from deployment.backup_storage import checksum
            if checksum(raw) != manifest['sha256']:
                raise ValueError('Source manifest mismatch')
            report = {'sha256': storage.upload(args.key, raw), 'readback_verified': True, 'restore_verified': False}
        elif args.action == 'download':
            if args.file is None or not args.key or not args.sha256:
                raise ValueError('New output file, key and trusted checksum required')
            raw = storage.download(args.key, args.sha256)
            with args.file.open('xb') as stream:
                stream.write(raw)
            report = {'download_verified': True}
        elif args.action == 'list':
            report = storage.list()
        else:
            report = {'deletion_candidates': storage.retention_plan(args.days), 'deleted': False}
        print(json.dumps(report, default=str))
        return 0
    except Exception as error:
        # SDK errors can contain endpoint/account details. Keep output sanitized.
        print(json.dumps({'error': 'storage_operation_failed', 'type': type(error).__name__}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
