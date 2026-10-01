# Local HTTPS federation setup

The local helper provisions credentials and launches the existing mutual-TLS
service/client. Run commands from `infra/` using the installed federation environment.

## 1. Provision once

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local provision
```

This creates ignored `federated/secrets/local-dev/` with a server bundle and three
separate node bundles, plus a monitoring-only certificate bundle without HMAC
keys for the [metrics endpoint](federated-monitoring.md). Certificates expire after seven days and the server
certificate accepts only `localhost` and `127.0.0.1`. Node certificates contain
their registered federation identity URIs. Each node has its own random HMAC key;
only the server bundle contains all three. The temporary CA private key is never
saved. No system trust store is changed and no network service is started.

On Windows, provisioning removes inherited permissions on the newly created
directory and grants the current Windows SID full access using `icacls`. Children
inherit that restriction. On POSIX, directories use mode 0700 and files 0600.
Administrators and other processes running as the same user remain outside this
protection boundary. No execution-policy setting is modified.

Existing bundles are never overwritten. Provisioning writes `manifest.json` last;
an interrupted bundle without this file cannot be launched. Use a fresh bundle
name after expiry or failed provisioning, for example `--bundle local-dev-2`.
The manifest prints only public metadata, never private keys or HMAC secrets.

## 2. Start the coordinator

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local server
```

This foreground process listens on `127.0.0.1:8443`. Leave its terminal open.
It closes rounds every 120 seconds and saves to
`federated/checkpoints/local-dev.json`. Existing checkpoints resume automatically.
Only one server may use this port/checkpoint. Ctrl+C stops it; pending updates
are discarded. This launcher does not create a background service.

## 3. Submit the three regional updates

In a second terminal, again from `infra/`, run within the same round:

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local client --node district-a
.\.venv-federated\Scripts\python.exe -m federated.local client --node district-b
.\.venv-federated\Scripts\python.exe -m federated.local client --node district-c
```

Each command trains the synthetic PyTorch model once and submits its signed
update. A `pending` response confirms admission; the server's later `aggregated`
message confirms aggregation. At least two valid clients are required. Submit
again only after the round closes; duplicate contributions are rejected. This is
a manual demonstration, not an automatic client scheduler or a healthcare model.

The launcher injects secrets only into the selected child process environment,
removes inherited credentials for the other role and disables inherited TLS key
logging. It does not change your terminal's environment or print secrets. It uses
absolute credential paths and runs from `infra/`, so no manual environment-variable
setup is needed. Node bundles still share one OS user in this local demonstration.

For a different bundle, pass the same `--bundle NAME` to provision, server and
client. Each name has a separate checkpoint; a fresh name starts fresh model state.
Copying/migrating checkpoints is not automatic. Do not distribute the entire bundle
to a node: it includes server credentials and other nodes' secrets.

## Validation and remaining work

One focused provisioning test checks certificate loading and node identities,
distinct HMAC keys, overwrite refusal and role-specific launcher environments.
It uses a temporary bundle and removes it afterward; it starts no listener and
trains no model. The earlier transport tests cover actual TLS communication.

```powershell
.\.venv-federated\Scripts\python.exe -m unittest federated.tests.test_local_credentials -v
```

Local provisioning uses `cryptography`, already supplied by the pinned Flower
environment. No persistent bundle has been provisioned as part of implementation
validation. Run step 1 when ready for the demo.

These credentials are for localhost development only. Production CA issuance,
secret-manager integration, rotation/revocation, rate limiting and deployment
hardening remain pending. See [HTTPS transport](federated-https.md) for the server's
limits and [signed admission](federated-authentication.md) for replay semantics.
