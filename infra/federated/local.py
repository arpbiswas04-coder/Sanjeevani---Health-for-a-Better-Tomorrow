"""Local-only credential provisioning and launch helpers. No deployment or training on provision."""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from optimization.common.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SECRET_ROOT = ROOT / "federated/secrets"
NODES = ("district-a", "district-b", "district-c")


def bundle_path(name):
    # A single safe directory component prevents arbitrary credential writes.
    if not name or len(name) > 64 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in name):
        raise ValidationError("Bundle name must contain lowercase letters, digits or hyphens")
    target = SECRET_ROOT / name
    if not target.resolve().is_relative_to(ROOT) or target.is_symlink():
        raise ValidationError("Credential bundle must stay inside infra")
    return target


def provision(name="local-dev"):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    target = bundle_path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(mode=0o700)  # Exclusive: never replace/rotate existing credentials.
    if os.name == "nt":
        identity = subprocess.run(["whoami.exe", "/user", "/fo", "csv", "/nh"],
                                  check=True, capture_output=True, text=True)
        sid = next(csv.reader(identity.stdout.splitlines()))[1]
        if not sid.startswith("S-1-") or any(c not in "S-0123456789" for c in sid):
            raise ValidationError("Cannot determine current Windows identity")
        # The new empty directory has only inherited rules. Remove them and grant
        # the current SID access, inherited by newly created child files/folders.
        subprocess.run(["icacls.exe", str(target), "/inheritance:r", "/grant:r", f"*{sid}:(OI)(CI)F"],
                       check=True, capture_output=True)
    else:
        target.chmod(0o700)

    def write(relative, data):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open("xb") as stream:
            stream.write(data)
        if os.name != "nt": path.chmod(0o600)

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=7)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Sanjeevani local development CA")])

    def issue(label, key, *, ca=False, san=None, eku=None):
        subject = ca_name if ca else x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, label)])
        builder = (x509.CertificateBuilder().subject_name(subject).issuer_name(ca_name)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=1)).not_valid_after(expires)
                   .add_extension(x509.BasicConstraints(ca=ca, path_length=0 if ca else None), True)
                   .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                       key_encipherment=False, data_encipherment=False, key_agreement=False,
                       key_cert_sign=ca, crl_sign=ca, encipher_only=False, decipher_only=False), True)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
                   .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False))
        if san is not None: builder = builder.add_extension(x509.SubjectAlternativeName(san), False)
        if eku is not None: builder = builder.add_extension(x509.ExtendedKeyUsage([eku]), False)
        return builder.sign(ca_key, hashes.SHA256())

    ca_pem = issue("ca", ca_key, ca=True).public_bytes(serialization.Encoding.PEM)

    def leaf(directory, label, san, eku):
        key = ec.generate_private_key(ec.SECP256R1())
        certificate = issue(label, key, san=san, eku=eku)
        write(f"{directory}/ca.pem", ca_pem)
        write(f"{directory}/cert.pem", certificate.public_bytes(serialization.Encoding.PEM))
        write(f"{directory}/key.pem", key.private_bytes(serialization.Encoding.PEM,
              serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))

    leaf("server", "localhost", [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))],
         ExtendedKeyUsageOID.SERVER_AUTH)
    keys = {node: secrets.token_hex(32) for node in NODES}
    leaf("monitor", "federation-monitor", [x509.UniformResourceIdentifier("urn:sanjeevani:monitor")],
         ExtendedKeyUsageOID.CLIENT_AUTH)
    write("server/node-keys.json", json.dumps(keys).encode())
    for node in NODES:
        directory = f"clients/{node}"
        leaf(directory, node, [x509.UniformResourceIdentifier(f"urn:sanjeevani:node:{node}")],
             ExtendedKeyUsageOID.CLIENT_AUTH)
        write(f"{directory}/signing-key.txt", keys[node].encode())
    manifest = {"purpose": "localhost-development-only", "expires_at": expires.isoformat(), "nodes": list(NODES)}
    # Written last: its presence denotes completed provisioning. CA private key is never saved.
    write("manifest.json", json.dumps(manifest, indent=2).encode())
    return {"bundle": str(target), **manifest}


def launch(name, role, node=None):
    target = bundle_path(name)
    manifest = json.loads((target / "manifest.json").read_text())
    if manifest.get("purpose") != "localhost-development-only" or datetime.fromisoformat(manifest["expires_at"]) <= datetime.now(timezone.utc):
        raise ValidationError("Incomplete or expired development bundle")
    environment = dict(os.environ)
    # Keep only the selected role's HMAC material in the child environment.
    for key in ("SANJEEVANI_NODE_KEYS_JSON", "SANJEEVANI_NODE_KEY_HEX", "SSLKEYLOGFILE"):
        environment.pop(key, None)
    if role == "server":
        directory = target / "server"
        environment["SANJEEVANI_NODE_KEYS_JSON"] = (directory / "node-keys.json").read_text()
        extra = ["--host", "127.0.0.1", "--checkpoint", str(ROOT / f"federated/checkpoints/{name}.json")]
        module = "federated.server.https"
    else:
        if node not in NODES: raise ValidationError("Unknown local node")
        directory = target / "clients" / node
        environment["SANJEEVANI_NODE_KEY_HEX"] = (directory / "signing-key.txt").read_text()
        extra = ["--url", "https://127.0.0.1:8443", "--node", node]
        module = "federated.clients.https"
    command = [sys.executable, "-m", module, "--ca", str(directory / "ca.pem"),
               "--cert", str(directory / "cert.pem"), "--key", str(directory / "key.pem"), *extra]
    return subprocess.call(command, cwd=ROOT, env=environment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("provision", "server", "client"))
    parser.add_argument("--bundle", default="local-dev")
    parser.add_argument("--node", choices=NODES)
    args = parser.parse_args()
    try:
        if args.action == "provision":
            print(json.dumps(provision(args.bundle), indent=2))
            return 0
        return launch(args.bundle, args.action, args.node)
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, KeyError, IndexError, TypeError, ImportError, subprocess.SubprocessError):
        print("local_federation_failed: check bundle name, permissions, expiry and dependencies; existing bundles are never overwritten")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
