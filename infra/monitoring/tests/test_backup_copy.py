"""Fail-closed copy checks using isolated synthetic files; no network activity."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from deployment import archive_copy
from deployment import backup_job
import subprocess


class BackupCopyTests(unittest.TestCase):
    def test_backup_failure_report_has_no_subprocess_secrets(self):
        for failure in (subprocess.CompletedProcess([], 2, '', 'SECRET'),
                        subprocess.TimeoutExpired('SECRET', 240)):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                kwargs = ({'side_effect': failure} if isinstance(failure, Exception)
                          else {'return_value': failure})
                with patch.object(backup_job, 'ROOT', root), patch('sys.argv', ['backup_job.py']), \
                        patch.object(backup_job.subprocess, 'run', **kwargs):
                    self.assertEqual(backup_job.main(), 2)
                reports = list(root.glob('outputs/backups/scheduled-*/failure.json'))
                self.assertEqual(len(reports), 1)
                self.assertNotIn('SECRET', reports[0].read_text())

    def test_readback_and_tamper_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'infra'
            source = root / 'outputs/backups/job'
            source.mkdir(parents=True)
            destination = Path(tmp) / 'mounted-destination'
            destination.mkdir()
            archive = source / 'backup.enc'
            archive.write_bytes(b'synthetic-encrypted-content')
            (source / 'manifest.json').write_text(json.dumps({
                'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}), encoding='utf-8')
            with patch.object(archive_copy, 'ROOT', root):
                target = archive_copy.copy_archive(archive, destination)
                self.assertEqual((target / 'backup.enc').read_bytes(), archive.read_bytes())
                self.assertFalse(json.loads((target / 'manifest.json').read_text())['off_host_durability_verified'])
                archive.write_bytes(b'tampered')
                with self.assertRaises(ValueError):
                    archive_copy.copy_archive(archive, destination)
                self.assertEqual(len(list(destination.iterdir())), 1)

    def test_missing_destination_refused(self):
        with self.assertRaises((ValueError, OSError)):
            archive_copy.copy_archive(Path('missing.enc'), Path('missing-destination'))
