# Local deployment tools

- `start-local.ps1`: Docker readiness, Compose validation, build/start and status.
- `prepare_local_env.py`: restricted database/JWT credentials, no overwrite.
- `prepare_demo_secrets.py`: missing Grafana/backup secrets in the restricted bundle.
- `verify_local.py`: endpoint, mTLS and monitoring acceptance report.
- `recovery_drill.py`: isolated synthetic encrypted PostgreSQL recovery check.
- `backup_job.py`: scheduler-ready backup and nondestructive retention plan.

See [startup](../docs/local-stack-start.md), [operations](../docs/operations-completion.md)
and [requirements](../docs/requirements-evidence.md). No Kubernetes, Helm, cloud
deployment or registered scheduled task is claimed in this directory.

## October 1 additions

See [complete setup and deployment instructions](../docs/completion-and-deployment.md)
for TLS ingress, local/S3 storage adapters, atomic operation status, exact-revision
CI gates, and guarded staging/production SSH deployment with rollback.
