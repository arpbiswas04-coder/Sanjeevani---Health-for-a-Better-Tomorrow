# Deployment, rollback and CI handoff

Local startup from infra: `deployment/start-local.ps1 -Observability -Grafana`.
Acceptance: `.\.venv-federated\Scripts\python.exe deployment/verify_local.py --observability --grafana`.
Use all five Compose files for subsequent operations: compose.yaml, compose.team.yaml,
compose.monitoring.yaml, compose.grafana.yaml and compose.observability.yaml.
Never use `down --volumes` for upgrade or rollback.

Before a release, the team records the current image IDs/digests and reviewed
configuration revision, preserves them under immutable tags, makes encrypted
database/config backups, and verifies a fresh-destination restore. Schema changes
need Member 2's explicit forward/backward compatibility plan; do not restore a
database over the running source as a shortcut.

For rollback, an operator creates an infra-local Compose override setting affected
services to those recorded prior image tags. Apply it last with `up -d --no-build
--pull never --wait`, then rerun acceptance. Restore only compatible configuration;
keep existing volumes and credentials. No prior release tag is invented here.
If schema compatibility is unknown, stop and involve Member 2 before switching.

The inactive CI template now builds/typechecks the actual frontend, statically
checks Python errors, runs existing backend and AI tests, verifies metrics failure
paths, and builds team images. Frontend has no lint/test scripts; the AI test
checks placeholders, not predictions. These missing gates remain team-owned.
Existing optimization/federation tests and failing-on-findings security jobs remain.
Hosted jobs have not run; template preparation is not passing CI evidence.

Team maintainer: review/copy the template to `.github/workflows/`, execute it,
address failures, then configure required checks and protected deployment
environments. Staging on develop and production on approved release require an
agreed hosting target, workload identity, secrets, migration/rollback plan and
security acceptance. No provider was selected, so no deploy command is invented.
