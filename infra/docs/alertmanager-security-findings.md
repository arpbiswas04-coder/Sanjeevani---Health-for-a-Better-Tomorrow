# Alertmanager local demo scan

2 HIGH/CRITICAL package/advisory occurrences in prom/alertmanager:v0.34.1. Report: outputs/security/alertmanager-image.json.

| Advisory | Package | Installed | Listed fix |
| --- | --- | --- | --- |
| CVE-2026-84445 | google.golang.org/grpc | v1.83.1 | 1.82.2, 1.83.2, 1.84.0-dev.0.20260825144003-d5a41119e0e3, 1.85.0-dev.0.20260825072537-93e31b48545e |
| CVE-2026-84445 | google.golang.org/grpc | v1.83.1 | 1.82.2, 1.83.2, 1.84.0-dev.0.20260825144003-d5a41119e0e3, 1.85.0-dev.0.20260825072537-93e31b48545e |

Upstream image maintainer / Member 4 follow-up. Local-only deployment does not waive findings. Receiver uses the separately scanned backend image.

## Remediated local image

Dockerfile.alertmanager rebuilds the official v0.34.1 source and UI with gRPC
v1.83.2, replacing both affected binaries. The image scan
`outputs/security/alertmanager-patched.json` exited zero with no HIGH/CRITICAL
findings. This is the recorded scanner scope, not a guarantee of no vulnerabilities.
The patched image is running and firing/resolved delivery passed again:
`outputs/alerts-pz9r7pyh.json`. Backend/federation findings are unaffected.
