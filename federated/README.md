# Federated learning — local foundation

Implemented: three synthetic regional clients, local gradient-descent training,
sample-weighted FedAvg, versioned rounds, update validation, minimum-participant
handling and node metadata. This is an in-process reference simulation, not a
networked federation or a health forecasting model.

From `infra/`:

```powershell
.\.venv\Scripts\python.exe -m federated --rounds 5
```

No external dependencies are required. See
[the foundation guide](../docs/federated-foundation.md) for the contract and
limitations. Config is in `configs/demo.json`. Six focused tests are in `tests/`.

Versioned atomic checkpoints and validated recovery are now available; see
[checkpoint commands and limitations](../docs/federated-checkpoints.md).

Optional Flower/PyTorch clients now run in three local subprocesses with synthetic
held-out evaluation and checkpoint support. See the
[regional adapter guide](../docs/flower-pytorch-regional.md) for its separate environment.

An opt-in [signed update admission layer](../docs/federated-authentication.md)
now verifies per-node keys and rejects replayed packets. Existing local runners
do not yet use it. A separate [mutual-TLS HTTPS service and client](../docs/federated-https.md)
now connect that boundary to synthetic PyTorch training. They require provisioned
certificates and node keys. The [local setup helper](../docs/federated-local-setup.md)
now creates restricted localhost credentials and launches each role without manual
environment-variable setup. Next: deployment hardening and integration
with a Member 3 model. Network isolation, secure aggregation and differential
privacy remain pending.
