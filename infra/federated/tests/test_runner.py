import unittest
from unittest.mock import Mock
from federated.clients.runner import run_rounds
from federated.strategies.fedavg import MODEL_SCHEMA


def state(round_id=1):
    return {"challenge": str(round_id) * 64, "round": round_id, "model_version": round_id - 1,
            "model_schema": MODEL_SCHEMA, "parameters": {"weight": 0, "bias": 0}}


class RunnerTests(unittest.TestCase):
    def test_once_per_challenge_and_timeout_without_retraining(self):
        now = [0]
        def sleep(seconds): now[0] += seconds
        client = Mock()
        client.round_request.return_value = state()
        client.submit.return_value = {"node_id": "a", "round": 1, "status": "pending"}
        train = Mock(return_value={"node_id": "a"})
        result = run_rounds(client, train, b"key", rounds=2, max_wait_seconds=30, clock=lambda: now[0], sleep=sleep)
        self.assertEqual(result["status"], "timeout")
        train.assert_called_once()
        client.submit.assert_called_once()

    def test_new_round_and_discard_stale_work(self):
        client = Mock()
        client.round_request.side_effect = [state(1), state(2), state(2), state(2)]
        client.submit.return_value = {"node_id": "a", "round": 2, "status": "pending"}
        result = run_rounds(client, lambda _: {"node_id": "a"}, b"key", sleep=lambda _: None)
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["discarded_stale_training"], 1)
        client.submit.assert_called_once()

    def test_submission_failure_is_not_retried(self):
        client = Mock()
        client.round_request.return_value = state()
        client.submit.side_effect = OSError("Lost acknowledgement")
        with self.assertRaises(OSError):
            run_rounds(client, lambda _: {"node_id": "a"}, b"key")
        client.submit.assert_called_once()
