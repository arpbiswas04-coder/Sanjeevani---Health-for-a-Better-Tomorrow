import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from federated.server.rate_limit import IdentityLimiter
from federated.server.https import Handler
from federated.server.metrics import Metrics


class RateLimitTests(unittest.TestCase):
    def test_refill_identity_isolation_and_bounded_state(self):
        now = [0.0]
        limiter = IdentityLimiter(["a", "b"], requests_per_minute=30, burst=2, clock=lambda: now[0])
        self.assertEqual([limiter.retry_after("a") for _ in range(3)], [0, 0, 2])
        self.assertEqual(limiter.retry_after("b"), 0)
        now[0] = 1
        self.assertEqual(limiter.retry_after("a"), 1)
        now[0] = 2
        self.assertEqual(limiter.retry_after("a"), 0)
        self.assertEqual(limiter.retry_after("unknown"), 60)
        self.assertEqual(len(limiter.buckets), 2)

    def test_limited_update_never_reaches_admission_or_body(self):
        handler = Handler.__new__(Handler)
        handler.path, handler.command = "/v1/updates", "POST"
        handler.connection = Mock()
        handler.connection.getpeercert.return_value = {"subjectAltName": [("URI", "urn:sanjeevani:node:a")]}
        handler.server = SimpleNamespace(nodes={"a"}, limiter=IdentityLimiter([("node", "a")], burst=1, clock=lambda: 0),
                                         metrics=Metrics(), admission=Mock())
        handler.server.limiter.retry_after(("node", "a"))
        handler.reply, handler.rfile = Mock(), Mock()
        handler.do_POST()
        handler.reply.assert_called_once_with(429, {"error": "rate_limited"}, retry_after=2)
        handler.rfile.read.assert_not_called()
        handler.server.admission.submit.assert_not_called()
        self.assertEqual(handler.server.metrics.rate_limited, 1)
