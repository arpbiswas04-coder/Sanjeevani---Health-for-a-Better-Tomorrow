# Member 4 delivery and remaining acceptance gates

## Fast demonstration

From the repository root:

```powershell
cd infra
.\.venv\Scripts\python.exe delivery.py
.\.venv\Scripts\python.exe delivery.py --demo
```

The first command only inventories prerequisites. The second runs ten bounded
synthetic CLI demos and saves their JSON outputs plus a summary in a new ignored
`infra/outputs/delivery-*` directory. It does not install packages, start services,
contact the backend, change real stock or run the full test suite. Its federation
step is one tiny standard-library reference round, not PyTorch training.

On September 30, 2026 all ten demos passed: redistribution, transport, routing,
ambulance, emergency scoring, emergency resource orchestration, workforce,
procurement, timeline comparison and reference federation. This confirms those
example CLI paths returned valid successful JSON; it is not exhaustive correctness,
clinical validation, production readiness or live cross-service integration.

## What can be handed over now

| Deliverable | Status and supporting guide |
| --- | --- |
| Recommendation engines | Standalone modules and synthetic examples implemented; [quickstart](member4-quickstart.md) |
| Backend inventory mapping | Read-only adapter and contract; [handoff](backend-handoff.md) |
| Simulation | Sequential surplus ledger, arrivals and scenario comparisons; [guide](timeline-comparison.md) |
| Federation | FedAvg reference, optional PyTorch adapters, checkpoints and multi-round clients; [runner](federated-round-runner.md) |
| Federation security | Mutual TLS, signed admission, replay protection and rate limits; [HTTPS](federated-https.md) |
| Local credentials | Restricted directory and short-lived demo certificates; [setup](federated-local-setup.md) |
| Container stack | Member 4 Compose configuration supplied; build/runtime not verified; [Docker](federated-docker.md) |
| Monitoring | Certificate-protected metrics, Prometheus rules, Grafana dashboard; rendering/scraping not verified; [monitoring](federated-monitoring.md) |
| Federation recovery | Encrypted backup and no-overwrite restore with focused recovery checks; [backup](federated-backup.md) |
| CI/security | Inactive test, isolated federation integration, audit and image-scan template; [scanning](security-scanning.md) |

## Mandatory unfinished work — do not mark complete

1. **Privacy:** differential privacy with clipping/noise, privacy accounting and
   utility evaluation; secure aggregation so the coordinator does not receive
   clear individual updates. TLS/HMAC do not implement either requirement.
2. **Member 2 integration:** actual authorized APIs, recommendation persistence,
   human approval, atomic stock reservation/rechecks and live roster/fleet data.
   These belong in the backend and cannot be completed through infra-only changes.
3. **Member 3 integration:** agreed forecast schemas, real model artifacts and
   eligible local training data. Current federation data/model are synthetic.
4. **Runtime acceptance:** install/use Docker on a suitable host, build images,
   run the Member 4 stack, verify certificates/volume permissions, inspect actual
   metrics/dashboard and then integrate the full team application stack.
5. **Active CI and deployment:** team places the reviewed template under root
   `.github/workflows/`, runs checks, addresses scanner findings and configures
   branch protection/staging. No hosted workflow, image scan or deployment is
   claimed to have run. Current actions/image versions still need release review.
6. **Disaster recovery:** database and object-storage backups, off-host retention,
   independently recoverable keys, and restore drills. Model checkpoints alone
   do not back up the application.

Other assignment items still need agreed scope: resilience orchestration,
cross-country/BRICS federation, optional personalization and richer digital-twin
behavior (multiple active batches, destination storage and travel delays).

## Team integration order

First demonstrate the existing engines using `delivery.py --demo`. Then Member 2
can implement the documented recommendation boundary while Member 3 supplies its
model/data contracts. In parallel on a Docker-capable host, verify Compose and
monitoring. Complete privacy mechanisms before claiming privacy-preserving training
on real health data. Activate CI and fix failures before an integration PR is merged.

All implementation changes in this work stay under `infra/`. Root application
files and workflow activation remain team-owned. No final estimate based on file
count should replace the acceptance gates above.
