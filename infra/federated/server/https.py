"""Private development HTTPS transport. Not a production HTTP server."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import ssl
import time

from federated.server.admission import AuthenticatedRounds, MAX_PACKET_BYTES
from federated.server.checkpoints import load_checkpoint
from federated.server.coordinator import Coordinator
from federated.server.metrics import Metrics, is_monitor
from federated.server.rate_limit import IdentityLimiter
from optimization.common.validation import ValidationError

IDENTITY_PREFIX = "urn:sanjeevani:node:"


def server_context(ca, cert, key):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(cafile=ca)
    context.load_cert_chain(cert, key)
    return context


class FederationServer(HTTPServer):
    """Sequential requests bound concurrency; handshake and I/O time out."""
    def __init__(self, address, admission, context, *, requests_per_minute=30, burst=10):
        self.admission = admission
        self.nodes = frozenset(admission.state()["nodes"])
        self.context = context
        self.metrics = Metrics()
        self.limiter = IdentityLimiter([("node", node) for node in self.nodes] + [("monitor", "metrics")],
                                       requests_per_minute=requests_per_minute, burst=burst)
        super().__init__(address, Handler)
        self.timeout = 1

    def get_request(self):
        sock, address = self.socket.accept()
        sock.settimeout(5)
        try:
            return self.context.wrap_socket(sock, server_side=True), address
        except BaseException:
            sock.close()
            raise

    def handle_error(self, request, client_address):
        # Never include packet bodies, credentials or request headers in logs.
        print("federation_request_failed", flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "FederationDev/1"
    sys_version = ""

    def log_message(self, format, *args):
        pass

    def reply(self, status, value, *, retry_after=None):
        if self.command == "POST" and self.path == "/v1/updates":
            if status == 202: self.server.metrics.accepted += 1
            elif status >= 400: self.server.metrics.rejected += 1
        raw = json.dumps(value, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        if retry_after is not None: self.send_header("Retry-After", str(retry_after))
        self.end_headers()
        self.close_connection = True
        self.wfile.write(raw)

    def allow_request(self, identity):
        wait = self.server.limiter.retry_after(identity)
        if wait:
            self.server.metrics.rate_limited += 1
            self.reply(429, {"error": "rate_limited"}, retry_after=wait)
            return False
        return True

    def identity(self):
        # Monitoring credentials must never participate in training.
        if any(kind == "URI" and value == "urn:sanjeevani:monitor" for kind, value in
               self.connection.getpeercert().get("subjectAltName", ())):
            self.reply(403, {"error": "participant_certificate_required"})
            return None
        names = [value[len(IDENTITY_PREFIX):] for kind, value in
                 self.connection.getpeercert().get("subjectAltName", ())
                 if kind == "URI" and value.startswith(IDENTITY_PREFIX)]
        if len(names) != 1 or names[0] not in self.server.nodes:
            self.reply(403, {"error": "unregistered_certificate_identity"})
            return None
        return names[0] if self.allow_request(("node", names[0])) else None

    def do_GET(self):
        if self.path == "/metrics":
            if not is_monitor(self.connection.getpeercert()):
                self.reply(403, {"error": "monitor_certificate_required"})
                return
            if not self.allow_request(("monitor", "metrics")): return
            raw = self.server.metrics.render(self.server.admission.state())
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            self.wfile.write(raw)
            return
        if self.identity() is None: return
        if self.path != "/v1/round":
            self.reply(404, {"error": "not_found"})
            return
        self.reply(200, self.server.admission.round_request())

    def do_POST(self):
        node = self.identity()
        if node is None: return
        if self.path != "/v1/updates":
            self.reply(404, {"error": "not_found"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get_all("Transfer-Encoding") or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self.reply(400, {"error": "invalid_body_framing"})
            return
        if len(lengths[0]) > 6 or not 1 <= int(lengths[0]) <= MAX_PACKET_BYTES:
            self.reply(413, {"error": "body_too_large"})
            return
        if self.headers.get_all("Content-Type") != ["application/json"]:
            self.reply(415, {"error": "json_required"})
            return
        try:
            raw = self.rfile.read(int(lengths[0]))
            if len(raw) != int(lengths[0]): raise ValidationError("Truncated body")
            result = self.server.admission.submit(raw, expected_node=node)
        except (ValidationError, TimeoutError):
            self.reply(400, {"error": "update_rejected"})
            return
        self.reply(202, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--round-seconds", type=int, default=120)
    parser.add_argument("--requests-per-minute", type=int, default=30)
    parser.add_argument("--request-burst", type=int, default=10)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[2]
        if not args.checkpoint.resolve().is_relative_to(root):
            raise ValidationError("Checkpoint must stay inside infra")
        if not 10 <= args.round_seconds <= 3600: raise ValidationError("Invalid round interval")
        config = json.loads((root / "federated/configs/demo.json").read_text())
        coordinator = load_checkpoint(args.checkpoint) if args.checkpoint.exists() else Coordinator(config["nodes"], min_clients=config["min_clients"])
        raw_keys = json.loads(os.environ["SANJEEVANI_NODE_KEYS_JSON"])
        keys = {node: bytes.fromhex(value) for node, value in raw_keys.items()}
        admission = AuthenticatedRounds(coordinator, keys)
        context = server_context(args.ca, args.cert, args.key)
        with FederationServer((args.host, args.port), admission, context,
                              requests_per_minute=args.requests_per_minute, burst=args.request_burst) as server:
            print("federation_https_ready", flush=True)
            deadline = time.monotonic() + args.round_seconds
            while True:
                server.handle_request()
                if time.monotonic() >= deadline:
                    started = time.monotonic()
                    result = admission.close_round()
                    server.metrics.closed(result, time.monotonic() - started)
                    admission.save(args.checkpoint)  # Stop on persistence failure.
                    server.metrics.last_checkpoint = time.time()
                    print(json.dumps({"round": result["round"], "status": result["status"]}), flush=True)
                    deadline = time.monotonic() + args.round_seconds
    except KeyboardInterrupt:
        return 0  # Pending updates are discarded, not silently aggregated.
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        print("federation_https_failed: check certificates, node keys, checkpoint and configuration")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
