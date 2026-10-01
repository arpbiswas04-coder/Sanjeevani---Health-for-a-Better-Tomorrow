"""One ephemeral localhost TLS integration check; no training or retained secrets."""

from datetime import datetime, timedelta, timezone
import http.client
import importlib.util
from pathlib import Path
import ssl
import tempfile
import threading
import unittest

from federated.clients.https import FederationClient
from federated.server.admission import AuthenticatedRounds
from federated.server.coordinator import Coordinator
from federated.server.https import FederationServer, server_context
from federated.strategies.fedavg import MODEL_SCHEMA
from optimization.common.validation import ValidationError


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "TLS fixture needs optional cryptography")
class HTTPSIntegrationTest(unittest.TestCase):
    def test_tls_identity_signed_updates_and_request_bounds(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as folder:
            root = Path(folder)
            ca_key = ec.generate_private_key(ec.SECP256R1())
            ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Ephemeral test CA")])
            now = datetime.now(timezone.utc)

            def issue(name, key, ca=False, san=None, eku=None):
                builder = (x509.CertificateBuilder().subject_name(name).issuer_name(ca_name)
                           .public_key(key.public_key()).serial_number(x509.random_serial_number())
                           .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
                           .add_extension(x509.BasicConstraints(ca=ca, path_length=0 if ca else None), True)
                           .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                               key_encipherment=False, data_encipherment=False, key_agreement=False,
                               key_cert_sign=ca, crl_sign=ca, encipher_only=False, decipher_only=False), True)
                           .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
                           .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False))
                if san is not None: builder = builder.add_extension(x509.SubjectAlternativeName(san), False)
                if eku is not None: builder = builder.add_extension(x509.ExtendedKeyUsage([eku]), False)
                return builder.sign(ca_key, hashes.SHA256())

            ca_path = root / "ca.pem"
            ca_path.write_bytes(issue(ca_name, ca_key, ca=True).public_bytes(serialization.Encoding.PEM))

            def leaf(label, san, eku):
                key = ec.generate_private_key(ec.SECP256R1())
                cert = issue(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, label)]), key, san=san, eku=eku)
                cert_path, key_path = root / f"{label}.pem", root / f"{label}.key"
                cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
                key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
                return str(cert_path), str(key_path)

            server_cert, server_key = leaf("server", [x509.DNSName("localhost")], ExtendedKeyUsageOID.SERVER_AUTH)
            client_certs = {node: leaf(node, [x509.UniformResourceIdentifier(f"urn:sanjeevani:node:{node}")],
                                      ExtendedKeyUsageOID.CLIENT_AUTH) for node in ("a", "b", "unknown")}
            keys = {"a": b"a" * 32, "b": b"b" * 32}
            admission = AuthenticatedRounds(Coordinator({"a": "east", "b": "west"}), keys)
            server = FederationServer(("127.0.0.1", 0), admission, server_context(str(ca_path), server_cert, server_key))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                clients = {node: FederationClient(f"https://localhost:{port}", ca=str(ca_path), cert=cert, key=key)
                           for node, (cert, key) in client_certs.items()}
                state = clients["a"].round_request()
                with self.assertRaises(ValidationError): clients["unknown"].round_request()
                cert, key = client_certs["a"]
                mismatch = FederationClient(f"https://127.0.0.1:{port}", ca=str(ca_path), cert=cert, key=key)
                with self.assertRaises(ssl.SSLCertVerificationError): mismatch.round_request()
                context = ssl.create_default_context(cafile=str(ca_path))
                connection = http.client.HTTPSConnection("localhost", port, context=context, timeout=5)
                try:
                    with self.assertRaises((OSError, http.client.HTTPException)):
                        connection.request("GET", "/v1/round")
                        connection.getresponse()
                finally:
                    connection.close()
                with self.assertRaises(ValidationError): clients["a"].request("POST", "/v1/updates", b"x" * 16385)
                with self.assertRaises(ValidationError): clients["a"].request("POST", "/v1/close", b"{}")
                update = {"node_id": "b", "round": state["round"], "model_version": state["model_version"],
                          "model_schema": MODEL_SCHEMA, "local_samples": 2, "training_duration_seconds": 0.1,
                          "parameters": {"weight": 1, "bias": 0.5}, "metrics": {"local_training_mse": 0.1}}
                with self.assertRaises(ValidationError): clients["a"].submit(update, state["challenge"], keys["b"])
                for node in ("a", "b"):
                    update["node_id"] = node
                    with self.assertRaises(ValidationError): clients[node].submit(update, state["challenge"], b"z" * 32)
                    self.assertEqual(clients[node].submit(update, state["challenge"], keys[node])["status"], "pending")
                    with self.assertRaises(ValidationError): clients[node].submit(update, state["challenge"], keys[node])
                self.assertEqual(admission.close_round()["status"], "aggregated")
                self.assertEqual(clients["a"].round_request()["model_version"], 1)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
