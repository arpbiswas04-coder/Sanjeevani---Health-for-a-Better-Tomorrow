# Local release setup — October 1, 2026

Selected target: local demonstration only. All changes remain inside infra, as
explicitly reconfirmed. Cloud credentials and real off-host storage are outside
this chosen target; no external account, upload or notification was activated.

## Run

From infra:

```powershell
deployment/start-local.ps1 -Alerts -Grafana
.\.venv-federated\Scripts\python.exe deployment/verify_local_alerts.py
ci-cd/check-local.ps1 -Runtime
```

Alerts implies the team, monitoring and observability overlays. For direct Compose
commands include compose.yaml, compose.team.yaml, compose.monitoring.yaml,
compose.grafana.yaml, compose.observability.yaml and compose.alerts.yaml, in order.
The local check runner executes Member 4 tests in their separate existing Python
environments. It does not install packages, suppress scanner findings or activate
GitHub. Runtime checks are optional because they require the stack to be running.

## Verified local alert delivery

Alertmanager 0.34.1 routes to a local receiver. The receiver keeps only aggregate
firing/resolved counts in memory, not alert payloads, and loses them on restart.
Both services publish only to loopback (9093 and 9094), run as non-root with
read-only roots and dropped capabilities. This unauthenticated local demo must
not be exposed publicly. The receiver reuses the backend image, whose unresolved
security findings remain applicable.

Synthetic firing and resolution both arrived: `outputs/alerts-y13lx_qp.json`.
Promtool validates the six alert rules and configuration; amtool validates the
local route/receiver. The test injects a synthetic alert into Alertmanager; it is
not evidence that every operational rule has been triggered. Configuration follows
the [official Alertmanager reference](https://prometheus.io/docs/alerting/latest/configuration/).

## Verified local backup copy

The encrypted config archive was copied into the separate directory
`outputs/backup-copy-demo/sanjeevani-5c1ed2c955d746b39d9150f9f193092e` and read back
with a matching checksum. Its receipt explicitly says off-host durability and
restore are not verified. Earlier source archive restore was verified separately.
Use `archive_copy.py --local-demo` only with destinations under
`outputs/backup-copy-demo`; real-copy mode still rejects destinations inside infra.
This is same-host simulation, not protection against losing this computer.

## Remaining security and CI limits

Official PyPI metadata rechecked: Flower 1.39.0 still requires cryptography
>=46.0.7,<47, while latest cryptography is 50.0.2. No incompatible upgrade was
forced. Sources: [Flower metadata](https://pypi.org/pypi/flwr/json) and
[cryptography metadata](https://pypi.org/pypi/cryptography/json).

The official Python Bookworm candidate was scanned as an alternative; it also
has unfixed HIGH/CRITICAL findings (`outputs/security/python-bookworm-candidate.json`).
It was not adopted. Existing backend/federation findings remain documented and
are not waived. Local demonstration is not production security clearance.

GitHub reads workflows from root `.github/workflows`, so hosted Member 4 CI cannot
be activated while keeping every change inside infra. The user selected that
restriction again; no root workflow, commit or push was performed. The prepared
template and executable local checks are the available deliverables in this scope.

The original Alertmanager image had two gRPC findings. Both were remediated
by rebuilding the official source with gRPC 1.83.2. The patched image scan
exited zero with no HIGH/CRITICAL findings; see alertmanager-security-findings.md. The updated encrypted
configuration backup includes all 13 files, including alert setup, and restored
byte-for-byte: outputs/backups/config-dg3z9ygm/manifest.json.

The updated 13-file archive was also copied and successfully decrypted at
outputs/backup-copy-demo/sanjeevani-ce2bebd6ffb34a6b80da8fff32b05758.
All decoded files match the original fresh restore; recovery-evidence.json records
this local-only verification.

Patched Alertmanager delivery evidence: outputs/alerts-pz9r7pyh.json.
The inactive CI image matrix includes this patched build. The local check runner
was syntax-validated; its entire suite was not rerun because only focused checks
were needed for these changes.
