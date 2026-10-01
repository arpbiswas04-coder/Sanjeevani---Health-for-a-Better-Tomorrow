import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from federated.demo import run_demo
from federated.server.checkpoints import load_checkpoint, save_checkpoint, MAX_BYTES
from federated.server.coordinator import Coordinator
from federated.tests.test_foundation import update
from optimization.common.validation import ValidationError


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.coordinator = Coordinator({"a": "a", "b": "b", "c": "c"})

    def test_roundtrip_preserves_minimum_versions_and_metadata(self):
        self.coordinator.aggregate_round([update("a", 1, 2, 1), update("b", 2, 3, 1)])
        save_checkpoint(self.coordinator, self.path)
        restored = load_checkpoint(self.path)
        self.assertEqual(restored.state(), self.coordinator.state())
        packet = update("a", 1, 1, 1)
        result = restored.aggregate_round([packet])
        self.assertEqual(result["accepted_nodes"], [])

    def test_insufficient_round_restores_and_can_continue(self):
        self.coordinator.aggregate_round([update("a", 1, 2, 1)])
        save_checkpoint(self.coordinator, self.path)
        restored = load_checkpoint(self.path)
        result = restored.aggregate_round([update("a", 1, 2, 1, 2), update("b", 1, 2, 1, 2)])
        self.assertEqual(result["output_model_version"], 1)

    def test_resumed_training_matches_uninterrupted_parameters(self):
        run_demo(2, checkpoint_path=self.path)
        resumed = run_demo(3, resume_path=self.path, checkpoint_path=self.path)
        full = run_demo(5)
        self.assertEqual(resumed["coordinator"]["parameters"], full["coordinator"]["parameters"])
        self.assertEqual(resumed["coordinator"]["model_version"], 5)

    def test_corruption_and_invalid_but_rehashed_state_rejected(self):
        save_checkpoint(self.coordinator, self.path)
        original = self.path.read_bytes()
        doc = json.loads(original)
        doc["payload"]["state"]["parameters"]["weight"] = 10
        self.path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(ValidationError): load_checkpoint(self.path)
        doc = json.loads(original)
        doc["payload"]["state"]["next_round"] = 0
        payload = json.dumps(doc["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        doc["sha256"] = hashlib.sha256(payload).hexdigest()
        self.path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(ValidationError): load_checkpoint(self.path)

    def test_failed_replace_preserves_previous_checkpoint_and_cleans_temp(self):
        save_checkpoint(self.coordinator, self.path)
        original = self.path.read_bytes()
        self.coordinator.aggregate_round([update("a", 1, 2, 1), update("b", 1, 2, 1)])
        with patch("federated.server.checkpoints.os.replace", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError): save_checkpoint(self.coordinator, self.path)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.path.parent.glob(".checkpoint-*.tmp")), [])

    def test_unrelated_duplicate_and_oversized_files_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{', b'x' * (MAX_BYTES + 1)):
            self.path.write_bytes(raw)
            with self.assertRaises(ValidationError): load_checkpoint(self.path)
        self.path.write_bytes(b"unrelated user content")
        with self.assertRaises(ValidationError): save_checkpoint(self.coordinator, self.path)
        self.assertEqual(self.path.read_bytes(), b"unrelated user content")
