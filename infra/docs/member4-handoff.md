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
| Container stack | Team scaffolds and federation built/started locally; [acceptance](local-demo-acceptance.md) |
| Monitoring | Authenticated metrics, successful scrape, validated rules and eight-panel dashboard API; visual inspection pending; [monitoring](federated-monitoring.md) |
| Federation recovery | Encrypted backup and no-overwrite restore with focused recovery checks; [backup](federated-backup.md) |
| CI/security | Inactive test, isolated federation integration, audit and image-scan template; [scanning](security-scanning.md) |

## Mandatory unfinished work — do not mark complete

1. **Privacy:** a separate synthetic reference now implements clipping, Gaussian
   noise, session accounting, utility comparison and fixed-roster pairwise masked
   aggregation. See [privacy limitations](federated-privacy.md). It is not wired
   into HTTPS training, audited, dropout-tolerant or approved for real health data.
2. **Member 2 integration:** actual authorized APIs, recommendation persistence,
   human approval, atomic stock reservation/rechecks and live roster/fleet data.
   These belong in the backend and cannot be completed through infra-only changes.
3. **Member 3 integration:** proposed [team contracts](team-integration-contracts.md)
   and a freshness/context-checked forecast adapter are supplied. Teammates must
   accept the contracts and supply real APIs, artifacts and eligible local data.
4. **Runtime acceptance:** local scaffolds and federation now run; six endpoint
   checks, three aggregated training rounds and a synthetic real PostgreSQL restore
   passed. Real business integration and visual dashboard inspection remain pending.
5. **Active CI and deployment:** team places the reviewed template under root
   `.github/workflows/`, runs checks, addresses scanner findings and configures
   branch protection/staging. Local dependency and image scans ran and found
   vulnerabilities. Hosted CI, staging and production remain pending.
6. **Disaster recovery:** encrypted local PostgreSQL backup and restore-to-new-DB
   tooling is supplied; [guide](local-database-recovery.md). Real synthetic rows
   and constraints survived an encrypted backup/restore in PostgreSQL 16. Real
   application recovery, object storage, off-host retention and independent keys remain pending.

The agreed immediate target is a [local Docker demo](local-stack-start.md).
`compose.team.yaml` adds the existing backend/frontend scaffolds, PostgreSQL and
Redis without editing teammates' files. Five focused privacy, forecast and mocked
database-recovery checks passed. Runtime evidence is recorded separately in
[local acceptance](local-demo-acceptance.md).

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
