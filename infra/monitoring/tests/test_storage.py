from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path:
    sys.path.insert(0, _infra)

from deployment.backup_storage import LocalBackupStorage, S3BackupStorage, checksum


class StorageTests(unittest.TestCase):
    def test_local_integrity_overwrite_retention_and_deletion_boundary(self):
        with tempfile.TemporaryDirectory() as root:
            store = LocalBackupStorage(root)
            digest = store.upload('one.enc', b'encrypted-fixture')
            self.assertEqual(store.download('one.enc', digest), b'encrypted-fixture')
            with self.assertRaises(FileExistsError): store.upload('one.enc', b'other')
            with self.assertRaises(ValueError): store.upload('../escape.enc', b'bad')
            with self.assertRaises(ValueError): store.cleanup(['one.enc'])
            self.assertEqual(store.retention_plan(1, now=datetime.now(timezone.utc)+timedelta(days=5)), [])
            Path(root, 'one.enc').write_bytes(b'tampered')
            with self.assertRaises(ValueError): store.download('one.enc', digest)
            store.cleanup(['one.enc'], confirmed=True)
            self.assertEqual(store.list(), [])

    def test_s3_readback_failure_and_pagination(self):
        client = Mock()
        client.get_object.return_value = {'Body': BytesIO(b'cipher'), 'ContentLength': 6}
        storage = S3BackupStorage('test-bucket', client=client)
        self.assertEqual(storage.upload('new.enc', b'cipher'), checksum(b'cipher'))
        self.assertEqual(client.put_object.call_args.kwargs['IfNoneMatch'], '*')
        client.get_object.return_value = {'Body': BytesIO(b'broken'), 'ContentLength': 6}
        with self.assertRaises(ValueError): storage.download('new.enc', checksum(b'cipher'))
        client.get_paginator.return_value.paginate.return_value = [
            {'Contents': [{'Key': 'sanjeevani-backups/one.enc', 'LastModified': datetime.now(timezone.utc)}]},
            {'Contents': [{'Key': 'sanjeevani-backups/other/nested.enc', 'LastModified': datetime.now(timezone.utc)}]}]
        self.assertEqual([r['key'] for r in storage.list()], ['one.enc'])
        client.put_object.side_effect = OSError('network unavailable')
        with self.assertRaises(OSError): storage.upload('new.enc', b'cipher')
        with self.assertRaises(ValueError): S3BackupStorage('test-bucket', endpoint='http://remote', client=client)
