# Member 4 — optimization, federation, and infrastructure

All Member 4 implementation files live inside this `infra/` directory.
Run the commands below from `infra/`, not from the repository root.

```powershell
cd infra
python -m optimization.redistribution --input optimization/redistribution/examples/three_facilities.json
python -m unittest discover -s optimization/tests -v
```

If Python is not on PATH, see the verified Windows command in the
[quickstart](docs/member4-quickstart.md).

## Contents

- `optimization/`: working redistribution engine, synthetic examples, and tests.
- `federated/`: three-region synthetic learning prototype with validated FedAvg.
- `docs/`: [backend contract](docs/redistribution-contract.md),
  [inventory adapter handoff](docs/backend-handoff.md),
  [multi-batch redistribution](docs/multi-batch-redistribution.md),
  [transport allocation with fixed dispatch costs](docs/transport-optimization.md),
  [vehicle routing](docs/vehicle-routing.md),
  [ambulance allocation](docs/ambulance-allocation.md),
  [emergency priority scoring](docs/emergency-priority.md),
  [priority-aware resource recommendations](docs/emergency-resource-recommendations.md),
  [staff redistribution](docs/workforce-redistribution.md),
  [procurement recommendations](docs/procurement-recommendations.md),
  [federated learning foundation](docs/federated-foundation.md),
  [federated checkpoint recovery](docs/federated-checkpoints.md),
  [Flower/PyTorch regional adapter](docs/flower-pytorch-regional.md),
  [signed federation update admission](docs/federated-authentication.md),
  [mutual-TLS federation service](docs/federated-https.md),
  [local credential setup and launch commands](docs/federated-local-setup.md),
  [Member 4 Docker stack](docs/federated-docker.md),
  [federation metrics and alerts](docs/federated-monitoring.md),
  [Grafana federation dashboard](docs/federated-grafana.md),
  [encrypted federation backup and recovery](docs/federated-backup.md),
  [dependency and image scanning](docs/security-scanning.md),
  [redistribution scenario simulation](docs/scenario-simulation.md),
  [sequential inventory simulation](docs/inventory-timeline.md),
  [baseline-versus-disruption timeline comparison](docs/timeline-comparison.md),
  [quickstart](docs/member4-quickstart.md), and
  [roadmap](docs/member4-roadmap.md).
- `ci-cd/`: proposed GitHub Actions workflow template.
- `pyproject.toml`: Python package configuration.

The optimizer returns recommendations only. Both versions support one medicine
and destination with linear per-unit transport costs. V1 uses one selected batch
per facility; v2 uses all eligible batches under a shared facility safety-stock
cap. Backend approval and atomic stock rechecks are required before
any resource movement. No inventory is modified by this module.

The read-only adapter in `optimization/redistribution/backend.py` now maps
Member 2's serialized inventory records into recommendations, with freshness,
recall, reservation, and facility safety-stock checks. Live backend route and
approval integration remain pending; see the handoff above.

The separate `optimization/transport/` module now supports multiple destinations,
shared source/batch limits and fixed dispatch costs using optional OR-Tools.
Run its example with `.venv\Scripts\python.exe -m optimization.transport --input
optimization/transport/example.json` from this folder. See its guide for
installation, normalized backend inputs and honest solver-limit reporting.

`optimization/routing/` now plans single-depot delivery routes with vehicle
capacities, service windows, waiting, shift limits and return-to-depot travel.
It reports unserved deliveries and actual matrix distances. It uses the same
OR-Tools installation; see the vehicle-routing guide for its separate input
contract and the remaining allocation-to-routing integration work.

`optimization/ambulance/` now filters ambulance eligibility and ranks suitable
vehicles by ETA, distance and ID. It includes alternatives, explicit rejection
reasons and expiry checks, using no additional dependency. Run the synthetic
example with `.venv\Scripts\python.exe -m optimization.ambulance --demo`.

`optimization/emergency/` now scores facility-level operational pressure using
versioned weights and normalized inputs. It returns factor contributions and
keeps missing/stale facilities unscored. Run the synthetic example with
`.venv\Scripts\python.exe -m optimization.emergency --demo`.

## CI limitation

`ci-cd/member4-ci.yml` is a template, not an active GitHub Actions workflow.
GitHub requires workflows under the root `.github/workflows/` directory.
The template sets its working directory to `infra` so the team can activate it
later through a separately agreed change outside this directory. Until then,
run the test commands locally.

## Planned infrastructure

Agree with Member 2 on backend startup, database, dependency versions, health
endpoints, and environment variables before defining shared Docker services.
Shared application deployment, access controls, monitoring, and backup/restore
are not implemented yet. Federation has a separate private-development mutual-TLS
HTTPS service; see its guide above. The CLI healthcheck confirms module execution only.
