import copy
import unittest

from federated.clients.client import SyntheticClient
from federated.demo import run_demo
from federated.server.coordinator import Coordinator
from federated.strategies.fedavg import MODEL_SCHEMA
from optimization.common.validation import ValidationError


def update(node, samples, weight, bias, round_id=1, version=0):
    return {"node_id": node, "round": round_id, "model_version": version, "model_schema": MODEL_SCHEMA,
            "local_samples": samples, "training_duration_seconds": 0.1,
            "parameters": {"weight": weight, "bias": bias}, "metrics": {"local_training_mse": 1.0}}


class FederationTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = Coordinator({"a": "region-a", "b": "region-b", "c": "region-c"})

    def test_exact_sample_weighted_aggregation_and_copy_isolation(self):
        packets = [update("a", 1, 2, 0), update("b", 3, 6, 4)]
        before = copy.deepcopy(packets)
        result = self.coordinator.aggregate_round(packets)
        self.assertEqual(result["parameters"], {"weight": 5, "bias": 3})
        self.assertEqual(result["output_model_version"], 1)
        self.assertEqual(packets, before)
        result["parameters"]["weight"] = 999
        self.assertEqual(self.coordinator.state()["parameters"]["weight"], 5)
        self.assertEqual(self.coordinator.state()["nodes"]["c"]["status"], "missing")

    def test_insufficient_round_keeps_model_and_advances_attempt(self):
        result = self.coordinator.aggregate_round([update("a", 2, 3, 4)])
        self.assertEqual(result["status"], "insufficient_participants")
        state = self.coordinator.state()
        self.assertEqual(state["model_version"], 0)
        self.assertEqual(state["next_round"], 2)
        result = self.coordinator.aggregate_round([update("a", 1, 2, 1, 2), update("b", 1, 2, 1, 2)])
        self.assertEqual(result["status"], "aggregated")

    def test_duplicate_packet_aborts_without_state_change(self):
        before = self.coordinator.state()
        packet = update("a", 1, 1, 1)
        with self.assertRaises(ValidationError): self.coordinator.aggregate_round([packet, packet])
        self.assertEqual(self.coordinator.state(), before)

    def test_malformed_stale_and_unregistered_updates_are_rejected(self):
        for field, value in (("model_schema", "other"), ("round", 2), ("model_version", 8),
                             ("local_samples", True), ("parameters", {"weight": float("nan"), "bias": 0}),
                             ("raw_data", [[1, 2]])):
            self.setUp()
            bad = update("a", 1, 1, 1)
            bad[field] = value
            result = self.coordinator.aggregate_round([bad, update("b", 1, 1, 1), update("stranger", 1, 1, 1)])
            self.assertEqual(result["status"], "insufficient_participants")
            self.assertEqual(len(result["rejected_updates"]), 2)

    def test_client_does_not_mutate_global_model_or_send_raw_samples(self):
        client = SyntheticClient("a", [(0, 1), (1, 3)])
        initial = {"weight": 0.0, "bias": 0.0}
        packet = client.train(initial, round_id=1, model_version=0)
        self.assertEqual(initial, {"weight": 0.0, "bias": 0.0})
        self.assertEqual(packet["local_samples"], 2)
        self.assertNotIn("samples", packet)
        self.assertLess(packet["metrics"]["local_training_mse"], client.training_mse(initial))

    def test_three_node_demo_completes_and_improves_training_error(self):
        result = run_demo(5)
        self.assertEqual(result["coordinator"]["model_version"], 5)
        self.assertEqual(len(result["coordinator"]["nodes"]), 3)
        for node, initial in result["initial_local_training_mse"].items():
            self.assertLess(result["final_local_training_mse"][node], initial)
