"""Federated client participant for edge healthcare nodes."""

class HospitalEdgeClient:
    """Represents a hospital or regional healthcare facility participant."""
    def __init__(self, client_id: str, server_address: str = "localhost:8080"):
        self.client_id = client_id
        self.server_address = server_address

    def fit_local(self, parameters, config):
        """Train model locally on private hospital EHR data without data leakage."""
        return parameters, 0, {}

    def evaluate_local(self, parameters, config):
        """Evaluate aggregated global weights on local facility dataset."""
        return 0.0, 0, {"accuracy": 0.0}
