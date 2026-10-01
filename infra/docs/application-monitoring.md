# Local application monitoring

From `infra/`, run `deployment/start-local.ps1 -Observability -Grafana`.
The Observability switch includes Team and Monitoring. Existing local credentials
must exist; `deployment/prepare_demo_secrets.py` creates only missing token files.
Then run `.\.venv-federated\Scripts\python.exe deployment/verify_local.py --observability --grafana`.

The infra-owned ASGI wrapper exposes `/internal/metrics` only with a bearer token
from the restricted local credential directory. Prometheus reads that token from
a read-only mount. Raw paths, identifiers, payloads and credentials are not labels.
HTTP calls/errors/latency record real requests, grouped into health/api/other.
Read-only PostgreSQL and Redis probes have connection/read/statement timeouts;
failure emits dependency up=0, with unavailable numeric values absent.

The backend runs as UID 1000 with read-only root filesystem, dropped capabilities
and no new privileges. It uses one worker: counters are in-process and reset on
restart. Multiple workers require a different collection design. The demo database
probe uses the existing app credential in a read-only session, not a separately
provisioned least-privilege monitoring database role.

Optimizer calls emit durations when invoked in this same process. Separate CLI
process observations are not automatically exported by the backend. Member 3 can
wrap actual inference with `optimization.common.telemetry.timed('prediction', 'inference')`.
Use the context manager around awaited work; the synchronous decorator does not
time async functions. Until these integrations run, their panels have no data.
No Celery queue metric exists because this stack has no Celery workload.

Prometheus uses the application and federation rule files (six alerts). The new
dashboard has nine panels covering HTTP, dependencies, optimization and prediction.
Its API was verified; visual rendering remains unverified. Alert receiver delivery
has not been activated. Thresholds are demo settings, not agreed production SLOs.

Frontend/backend HTTP and bearer metrics are limited to this local development
network; they are not a public HTTPS deployment. Federation uses mutual TLS.
Prometheus is loopback-published and Grafana requires its local admin password.
Do not expose these endpoints publicly without reviewed ingress authentication/TLS.

September 30 evidence: ten endpoint checks passed in
`outputs/acceptance-7dt88lx2.json`; both Prometheus configurations/rules validated.
Ten synthetic CLI demos passed in `outputs/delivery-qlgyb6ht`.
