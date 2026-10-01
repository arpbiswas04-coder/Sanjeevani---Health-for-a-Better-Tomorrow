"""Bounded encrypted-archive storage. No key material, overwrite or automatic deletion."""
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

LIMIT = 96 * 1024 * 1024


def object_key(key):
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,96}\.enc', key):
        raise ValueError('Use a single safe encrypted archive name')
    return key


def checksum(raw):
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= LIMIT:
        raise ValueError('Archive size outside supported bounds')
    return hashlib.sha256(raw).hexdigest()


class BackupStorage:
    def retention_plan(self, days, *, now=None, keep_minimum=1):
        if type(days) is not int or not 1 <= days <= 3650 or type(keep_minimum) is not int or keep_minimum < 1:
            raise ValueError('Invalid retention settings')
        cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
        items = sorted(self.list(), key=lambda row: row['modified_at'], reverse=True)
        return [row['key'] for row in items[keep_minimum:] if row['modified_at'] < cutoff]

    def cleanup(self, keys, *, confirmed=False):
        if confirmed is not True or not isinstance(keys, list) or len(keys) > 1000:
            raise ValueError('Explicit reviewed deletion list required')
        # Never called automatically by a backup job.
        for key in keys:
            self.delete(object_key(key))


class LocalBackupStorage(BackupStorage):
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError('Provision a storage directory first')

    def path(self, key):
        path = self.root / object_key(key)
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise ValueError('Storage links are prohibited')
        return path

    def upload(self, key, raw):
        digest = checksum(raw)
        with self.path(key).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.download(key, digest)
        return digest

    def download(self, key, expected_sha256):
        with self.path(key).open('rb') as stream:
            raw = stream.read(LIMIT + 1)
        if checksum(raw) != expected_sha256:
            raise ValueError('Archive checksum mismatch')
        return raw

    def list(self):
        return [{'key': p.name, 'modified_at': datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)}
                for p in self.root.glob('*.enc') if p.is_file() and not p.is_symlink()]

    def delete(self, key):
        self.path(key).unlink()


class S3BackupStorage(BackupStorage):
    def __init__(self, bucket, *, prefix='sanjeevani-backups/', endpoint=None, client=None):
        if not isinstance(bucket, str) or not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', bucket):
            raise ValueError('Invalid bucket')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}/', prefix):
            raise ValueError('A dedicated single-directory prefix is required')
        if endpoint:
            url = urlsplit(endpoint)
            if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError('S3 endpoint must use HTTPS without credentials')
        self.bucket, self.prefix = bucket, prefix
        if client is None:
            import boto3
            from botocore.config import Config
            # Workload identity or standard AWS credential chain; no secret printing.
            client = boto3.client('s3', endpoint_url=endpoint,
                config=Config(connect_timeout=5, read_timeout=30, retries={'max_attempts': 3},
                              s3={'addressing_style': 'path'}))
        self.client = client

    def upload(self, key, raw):
        digest = checksum(raw)
        self.client.put_object(Bucket=self.bucket, Key=self.prefix + object_key(key), Body=raw,
                               Metadata={'sha256': digest}, ContentType='application/octet-stream', IfNoneMatch='*')
        self.download(key, digest)  # Verify bytes, not multipart ETag assumptions.
        return digest

    def download(self, key, expected_sha256):
        response = self.client.get_object(Bucket=self.bucket, Key=self.prefix + object_key(key))
        stream = response['Body']
        try:
            if response.get('ContentLength', LIMIT + 1) > LIMIT:
                raise ValueError('Remote archive exceeds bounds')
            raw = stream.read(LIMIT + 1)
        finally:
            stream.close()
        if checksum(raw) != expected_sha256:
            raise ValueError('Remote archive checksum mismatch')
        return raw

    def list(self):
        rows = []
        paginator = self.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            for item in page.get('Contents', []):
                name = item['Key'][len(self.prefix):]
                if re.fullmatch(r'[A-Za-z0-9_-]{1,96}\.enc', name):
                    rows.append({'key': name, 'modified_at': item['LastModified']})
                    if len(rows) > 10000:
                        raise ValueError('Inventory exceeds demo storage limit')
        return rows

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=self.prefix + object_key(key))


def configured_storage():
    mode = os.environ.get('BACKUP_STORAGE_MODE')
    if mode == 'local':
        return LocalBackupStorage(os.environ['BACKUP_LOCAL_DIRECTORY'])
    if mode == 's3':
        return S3BackupStorage(os.environ['S3_BUCKET'], endpoint=os.environ.get('S3_ENDPOINT'))
    raise ValueError('Select BACKUP_STORAGE_MODE=local or s3 explicitly')
