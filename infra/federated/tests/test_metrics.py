import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from federated.server.https import Handler
from federated.server.metrics import Metrics, MONITOR_URI
from federated.server.coordinator import Coordinator
from federated.server.rate_limit import IdentityLimiter


class MetricsTests(unittest.TestCase):
    def handler(self, uri, path="/metrics"):
        handler = Handler.__new__(Handler)
        handler.path, handler.command = path, "GET"
        handler.connection = Mock()
        handler.connection.getpeercert.return_value = {"subjectAltName": [("URI", uri)]}
        handler.server = SimpleNamespace(metrics=Metrics(), admission=Coordinator({"a": "east"}, min_clients=1), nodes={"a"})
        handler.server.limiter = IdentityLimiter([("node", "a"), ("monitor", "metrics")])
        handler.send_response, handler.send_header, handler.end_headers = Mock(), Mock(), Mock()
        handler.wfile = io.BytesIO()
        return handler

    def test_monitor_only_metrics_and_no_training_access(self):
        handler = self.handler(MONITOR_URI)
        handler.do_GET()
        handler.send_response.assert_called_with(200)
        self.assertIn(b"sanjeevani_federation_model_version 0", handler.wfile.getvalue())
        for path in ("/v1/round", "/v1/updates"):
            handler = self.handler(MONITOR_URI, path)
            if path.endswith("updates"):
                handler.command = "POST"
                handler.do_POST()
            else:
                handler.do_GET()
            handler.send_response.assert_called_with(403)
        handler = self.handler("urn:sanjeevani:node:a")
        handler.do_GET()
        handler.send_response.assert_called_with(403)

    def test_metrics_count_rounds_without_model_contents(self):
        metrics = Metrics()
        metrics.closed({"status": "insufficient_participants"}, 0.25)
        text = metrics.render(Coordinator({"a": "east"}, min_clients=1).state()).decode()
        self.assertIn("sanjeevani_federation_rounds_insufficient_total 1\n", text)
        self.assertIn("sanjeevani_federation_nodes_registered 1\n", text)
        self.assertNotIn("weight", text)
        self.assertNotIn("bias", text)
