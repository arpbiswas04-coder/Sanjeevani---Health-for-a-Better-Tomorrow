import importlib.util
from pathlib import Path
import tempfile
import unittest

from federated.backup import backup, restore, inspect_backup, ROOT
from federated.server.checkpoints import save_checkpoint, load_checkpoint
from federated.server.coordinator import Coordinator
from optimization.common.validation import ValidationError


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "Optional cryptography dependency required")
class BackupRecoveryTest(unittest.TestCase):
    def test_recovery_tamper_wrong_key_and_no_overwrite(self):
        from cryptography.fernet import Fernet
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            root = Path(folder)
            source, encrypted, recovered = root / "source.json", root / "copy.enc", root / "recovered.json"
            coordinator = Coordinator({"a": "east", "b": "west"})
            coordinator.aggregate_round([])
            save_checkpoint(coordinator, source)
            key = Fernet.generate_key()
            backup(source, encrypted, key)
            self.assertNotIn(b'"state"', encrypted.read_bytes())
            restore(encrypted, recovered, key)
            self.assertEqual(load_checkpoint(recovered).state(), coordinator.state())
            with self.assertRaises(FileExistsError): restore(encrypted, recovered, key)
            with self.assertRaises(FileExistsError): backup(source, encrypted, key)
            with self.assertRaises(ValidationError): inspect_backup(encrypted, Fernet.generate_key())
            damaged = bytearray(encrypted.read_bytes())
            damaged[len(damaged)//2] ^= 1
            encrypted.write_bytes(damaged)
            refused = root / "refused.json"
            with self.assertRaises(ValidationError): restore(encrypted, refused, key)
            self.assertFalse(refused.exists())
