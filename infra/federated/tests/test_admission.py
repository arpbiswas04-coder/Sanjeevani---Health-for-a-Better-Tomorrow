import json
import unittest

from federated.server.admission import AuthenticatedRounds, sign_update
from federated.server.coordinator import Coordinator
from federated.strategies.fedavg import MODEL_SCHEMA
from optimization.common.validation import ValidationError


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.keys = {"a": b"a" * 32, "b": b"b" * 32}  # Test-only keys.
        self.gate = AuthenticatedRounds(Coordinator({"a": "east", "b": "west"}), self.keys)

    def packet(self, node="a", **changes):
        request = self.gate.round_request()
        update = {"node_id": node, "round": request["round"], "model_version": request["model_version"],
                  "model_schema": MODEL_SCHEMA, "local_samples": 2, "training_duration_seconds": 0.1,
                  "parameters": {"weight": 1, "bias": 0.5}, "metrics": {"local_training_mse": 0.1}}
        update.update(changes)
        return sign_update(update, request["challenge"], self.keys[node], now=1000)

    def test_valid_round_and_replay_rejection(self):
        packet = self.packet()
        self.gate.submit(packet, now=1000)
        with self.assertRaises(ValidationError): self.gate.submit(packet, now=1000)
        self.gate.submit(self.packet("b"), now=1000)
        self.assertEqual(self.gate.close_round()["status"], "aggregated")
        self.assertEqual(self.gate.state()["model_version"], 1)
        with self.assertRaises(ValidationError): self.gate.submit(packet, now=1000)

    def test_tampering_impersonation_age_and_version_fail_without_consuming_slot(self):
        valid = self.packet()
        altered = json.loads(valid)
        altered["payload"]["update"]["parameters"]["weight"] = 9
        impersonated = json.loads(valid)["payload"]["update"]
        impersonated["node_id"] = "b"
        forged = sign_update(impersonated, self.gate.round_request()["challenge"], self.keys["a"], now=1000)
        for raw, now in ((json.dumps(altered).encode(), 1000), (forged, 1000),
                         (valid, 1121), (valid, 969), (self.packet(model_version=8), 1000)):
            with self.assertRaises(ValidationError): self.gate.submit(raw, now=now)
        self.assertEqual(self.gate.submit(valid, now=1000)["status"], "pending")

    def test_restart_and_malformed_packets(self):
        packet = self.packet()
        restored = AuthenticatedRounds(Coordinator.from_state(self.gate.state()), self.keys)
        with self.assertRaises(ValidationError): restored.submit(packet, now=1000)
        for raw in (b"{}", b"{" * 2000, b" " * 16385, b'{"payload":1,"payload":2,"signature":"x"}'):
            with self.assertRaises(ValidationError): self.gate.submit(raw, now=1000)
        self.assertEqual(self.gate.close_round()["status"], "insufficient_participants")
        self.assertEqual(self.gate.state()["model_version"], 0)
