# Member 4 Docker development stack

`infra/compose.yaml` defines the federation coordinator and three on-demand
regional clients. It uses the existing authenticated HTTPS and PyTorch modules.
This is a separate Member 4 development stack, not the complete application stack.
The root Compose file and other members' services are unchanged.

## Prepare and start

Use Docker with Linux containers and Compose v2. From `infra/`:

```powershell
# Once only; skip if this unexpired bundle already exists.
.\.venv-federated\Scripts\python.exe -m federated.local provision

# Validate configuration, then build and start the coordinator.
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml up --build -d federation-server
docker compose -f compose.yaml ps
```

Provisioning refuses to overwrite credentials. See [local setup](federated-local-setup.md)
for expiry and bundle handling. Compose currently mounts the `local-dev` bundle
explicitly. To use a fresh bundle, update all four source mounts together in a
local Compose override; never mix credentials from independently provisioned CAs.

The image runs as UID 1000 by default. On native Linux, set `MEMBER4_UID` to your
non-root host UID before building so it can read your mode-0700 credential bundle.
On Docker Desktop, ensure file sharing permits access to the credential directory.
Do not resolve permission failures by making private keys world-readable. Changing
UID later also requires deliberate migration of the existing checkpoint volume's
ownership; do not delete model state to work around permissions.

## Submit a round

After the server is healthy, run these in the same 120-second round window:

```powershell
docker compose -f compose.yaml run --rm --no-deps federation-client-a
docker compose -f compose.yaml run --rm --no-deps federation-client-b
docker compose -f compose.yaml run --rm --no-deps federation-client-c
docker compose -f compose.yaml logs --tail 30 federation-server
```

Clients train once and exit. They are under the `training` profile, so an ordinary
`up` starts only the server. Wait for the next round before submitting again.
At least two valid updates are needed for aggregation. No automatic training loop
or health-model integration is supplied.

Stop containers while retaining checkpoints:

```powershell
docker compose -f compose.yaml down
```

Do not add `--volumes` unless intentionally discarding saved model state.
The named checkpoint volume is separate from your host CLI checkpoints; no
automatic migration is performed. Credentials remain on the host.

## Isolation and limits

- Only `127.0.0.1:8443` is published on the host.
- Clients share the coordinator's network namespace to use its existing localhost
  certificate. They do not have isolated network identities; this is a local demo.
- Each client mounts only its own credential directory, read-only. The server
  receives its own certificate and the node HMAC registry.
- Containers run non-root with a read-only root filesystem, dropped capabilities,
  no-new-privileges, bounded memory/processes and rotating Docker logs.
- Checkpoints are writable only in the server's named volume; temporary files use
  a bounded tmpfs. Secrets, environments and checkpoint files are excluded from
  the image build context using `infra/.dockerignore`.
- The healthcheck proves TCP listener liveness only. It does not verify TLS
  credentials, successful aggregation, persistence or model quality.
- Images use pinned direct Python dependencies, but base tags and transitive
  dependencies are not digest/hash locked. Reproducible release builds and image
  scanning remain pending.

Docker was unavailable during implementation. YAML parsing, role mounts, build
paths and Python entrypoint syntax were checked; image builds and container
execution remain unverified. No images were downloaded and no training ran.

Next: verify this stack with Docker, then connect the team's application services,
add metrics/alerts, image scanning and backup/restore procedures. This does not
make the development HTTP service suitable for public production deployment.

References: Docker's [Compose profiles](https://docs.docker.com/compose/how-tos/profiles/)
and [build-context exclusions](https://docs.docker.com/build/concepts/context/#dockerignore-files).
