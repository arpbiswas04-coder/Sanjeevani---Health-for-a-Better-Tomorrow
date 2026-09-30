"""Read only this container's mounted credentials; replace process for signals."""
import os
from pathlib import Path
import sys

def main():
    role = sys.argv[1:]
    directory = Path("/run/federation")
    environment = dict(os.environ)
    for name in ("SANJEEVANI_NODE_KEYS_JSON", "SANJEEVANI_NODE_KEY_HEX", "SSLKEYLOGFILE"):
        environment.pop(name, None)
    if role == ["server"]:
        environment["SANJEEVANI_NODE_KEYS_JSON"] = (directory / "node-keys.json").read_text()
        module = "federated.server.https"
        arguments = ["--host", "0.0.0.0", "--checkpoint", "/app/infra/federated/checkpoints/compose.json"]
    elif role == ["privacy"]:
        os.execve(sys.executable, [sys.executable, "-m", "federated.privacy"], environment)
    elif len(role) == 2 and role[0] == "client" and role[1] in ("district-a", "district-b", "district-c"):
        environment["SANJEEVANI_NODE_KEY_HEX"] = (directory / "signing-key.txt").read_text()
        module = "federated.clients.https"
        arguments = ["--url", "https://127.0.0.1:8443", "--node", role[1],
                     "--rounds", environment.get("FEDERATION_CLIENT_ROUNDS", "1"),
                     "--max-wait-seconds", environment.get("FEDERATION_CLIENT_MAX_WAIT_SECONDS", "600")]
    else:
        raise ValueError("Invalid container role")
    command = [sys.executable, "-m", module, "--ca", str(directory / "ca.pem"),
               "--cert", str(directory / "cert.pem"), "--key", str(directory / "key.pem"), *arguments]
    os.execve(sys.executable, command, environment)

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError):
        print("federation_container_start_failed: check role and mounted credentials", file=sys.stderr)
        raise SystemExit(2)
