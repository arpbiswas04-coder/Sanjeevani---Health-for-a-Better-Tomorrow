"""Verified mutual-TLS client; no plaintext, redirect or insecure fallback."""

import argparse
import http.client
import json
import os
import ssl
from urllib.parse import urlsplit

from federated.server.admission import sign_update
from optimization.common.validation import ValidationError


class FederationClient:
    def __init__(self, url, *, ca, cert, key):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
            raise ValidationError("Use an HTTPS origin URL without credentials or path")
        self.host, self.port = parsed.hostname, parsed.port or 443
        self.context = ssl.create_default_context(cafile=ca)
        self.context.keylog_filename = None
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.context.load_cert_chain(cert, key)

    def request(self, method, path, raw=None):
        connection = http.client.HTTPSConnection(self.host, self.port, context=self.context, timeout=10)
        try:
            connection.request(method, path, body=raw,
                               headers={"Content-Type": "application/json"} if raw is not None else {})
            response = connection.getresponse()
            body = response.read(16385)
            if len(body) > 16384 or response.status not in (200, 202):
                raise ValidationError(f"Federation request rejected (HTTP {response.status})")
            return json.loads(body)
        finally:
            connection.close()

    def round_request(self):
        return self.request("GET", "/v1/round")

    def submit(self, update, challenge, signing_key):
        return self.request("POST", "/v1/updates", sign_update(update, challenge, signing_key))


def main():
    parser = argparse.ArgumentParser(description="Submit one synthetic PyTorch regional update over mutual TLS")
    parser.add_argument("--url", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    args = parser.parse_args()
    try:
        client = FederationClient(args.url, ca=args.ca, cert=args.cert, key=args.key)
        signing_key = bytes.fromhex(os.environ["SANJEEVANI_NODE_KEY_HEX"])
        state = client.round_request()
        from federated.strategies.fedavg import MODEL_SCHEMA
        if state.get("model_schema") != MODEL_SCHEMA:
            raise ValidationError("Unsupported server model schema")
        # Reuse the tested PyTorch adapter. Local samples never enter HTTP packets.
        os.environ["FLWR_TELEMETRY_ENABLED"] = "0"
        from federated.clients.regional_worker import execute
        result = execute({"node_id": args.node, "action": "fit", "parameters": state["parameters"],
                          "round": state["round"], "model_version": state["model_version"]})
        print(json.dumps(client.submit(result["update"], state["challenge"], signing_key)))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError, http.client.HTTPException):
        print("federation_client_failed: check credentials, server response and optional dependencies")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
