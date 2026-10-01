"""Provisioning check only: no listener or training process."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from federated import local
from federated.clients.https import FederationClient
from federated.server.https import server_context


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "Optional federation environment required")
class LocalCredentialTests(unittest.TestCase):
    def test_provision_permissions_certificates_and_role_launch(self):
        from cryptography import x509
        local.SECRET_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local.SECRET_ROOT) as temporary:
            with patch.object(local, "SECRET_ROOT", Path(temporary)):
                result = local.provision("check")
                target = Path(result["bundle"])
                with self.assertRaises(FileExistsError): local.provision("check")
                keys = json.loads((target / "server/node-keys.json").read_text())
                self.assertEqual(set(keys), set(local.NODES))
                self.assertEqual(len(set(keys.values())), 3)
                server = target / "server"
                server_context(str(server / "ca.pem"), str(server / "cert.pem"), str(server / "key.pem"))
                for node in local.NODES:
                    client = target / "clients" / node
                    self.assertEqual((client / "signing-key.txt").read_text(), keys[node])
                    self.assertFalse((client / "node-keys.json").exists())
                    cert = x509.load_pem_x509_certificate((client / "cert.pem").read_bytes())
                    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
                    self.assertEqual(san.get_values_for_type(x509.UniformResourceIdentifier), [f"urn:sanjeevani:node:{node}"])
                    FederationClient("https://127.0.0.1:8443", ca=str(client / "ca.pem"),
                                     cert=str(client / "cert.pem"), key=str(client / "key.pem"))
                with patch.dict(local.os.environ, {"SANJEEVANI_NODE_KEYS_JSON": "inherited", "SSLKEYLOGFILE": "unwanted"}):
                    with patch.object(local.subprocess, "call", return_value=0) as call:
                        local.launch("check", "client", "district-a")
                        env = call.call_args.kwargs["env"]
                        self.assertNotIn("SANJEEVANI_NODE_KEYS_JSON", env)
                        self.assertNotIn("SSLKEYLOGFILE", env)
                        self.assertEqual(env["SANJEEVANI_NODE_KEY_HEX"], keys["district-a"])
                        local.launch("check", "server")
                        env = call.call_args.kwargs["env"]
                        self.assertNotIn("SANJEEVANI_NODE_KEY_HEX", env)
                        self.assertEqual(json.loads(env["SANJEEVANI_NODE_KEYS_JSON"]), keys)
