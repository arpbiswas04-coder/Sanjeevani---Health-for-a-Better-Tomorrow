"""Federated aggregation server coordinator module."""

class FederatedServer:
    """Coordinator server for federated learning rounds."""
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port

    def start(self):
        """Start aggregation server (Flower / NVFlare compatible)."""
        print(f"Federated server listening at {self.host}:{self.port}")
