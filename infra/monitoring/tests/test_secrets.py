from pathlib import Path
import sys
import tempfile
import unittest

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path:
    sys.path.insert(0, _infra)

from monitoring.runtime.secret_injection import inject
from security import check_tracked_secrets as scan
from unittest.mock import patch


class SecretTests(unittest.TestCase):
    def test_injection_is_allowlisted_and_rejects_ambiguity(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'secret';path.write_text('test-only-secret\n')
            env={'JWT_SECRET_FILE':str(path),'UNRELATED_FILE':str(path)}
            inject(env)
            self.assertEqual(env['JWT_SECRET'],'test-only-secret')
            self.assertNotIn('UNRELATED',env)
            with self.assertRaises(ValueError): inject(env)
            path.write_text('')
            with self.assertRaises(ValueError): inject({'JWT_SECRET_FILE':str(path)})

    def test_scanner_detects_private_material_and_runtime_paths(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(scan,'ROOT',Path(folder)):
            path=Path(folder)/'example.txt'
            path.write_bytes(b'-----BEGIN '+b'PRIVATE KEY-----\nexample')
            self.assertTrue(scan.violations(Path('example.txt')))
            self.assertTrue(scan.violations(Path('infra/.env')))
            self.assertTrue(scan.violations(Path('infra/federated/secrets/node.key')))
            path.write_text('No private contents')
            self.assertFalse(scan.violations(Path('example.txt')))
