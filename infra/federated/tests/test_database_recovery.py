import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "Optional cryptography required")
class DatabaseRecoveryTests(unittest.TestCase):
    def test_encrypted_backup_and_fresh_restore_command_only(self):
        from cryptography.fernet import Fernet
        from security import postgres_recovery as recovery
        secret_root = recovery.ROOT / "federated/secrets"
        secret_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=secret_root) as folder:
            root = Path(folder)
            key = root / "backup.key"
            key.write_bytes(Fernet.generate_key())
            archive = root / "database.enc"
            calls = []
            def invoke(command, output=None):
                calls.append(command)
                if output is not None: output.write(b"PGDMPsynthetic-fixture-not-a-real-dump")
            common = ["--user", "sanjeevani", "--key-file", str(key), "--file", str(archive)]
            with patch.object(recovery.shutil, "which", return_value="mock-tool"), patch.object(recovery, "invoke", side_effect=invoke), contextlib.redirect_stdout(io.StringIO()):
                with patch("sys.argv", ["recovery", "backup", "--database", "sanjeevani", *common]):
                    self.assertEqual(recovery.main(), 0)
                self.assertFalse(archive.read_bytes().startswith(b"PGDMP"))
                with patch("sys.argv", ["recovery", "restore-drill", *common]):
                    self.assertEqual(recovery.main(), 0)
            created = next(command for command in calls if command[0] == "createdb")[-1]
            self.assertTrue(created.startswith("member4_restore_"))
            restore = calls[-1]
            self.assertEqual(restore[restore.index("--dbname") + 1], created)
            self.assertIn("--single-transaction", restore)
            self.assertNotIn("--clean", restore)
