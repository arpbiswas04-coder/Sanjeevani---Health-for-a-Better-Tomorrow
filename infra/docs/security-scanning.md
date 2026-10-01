# Member 4 dependency and image scanning

> Historical baseline below. October 1 implementation now includes root CI and
> guarded deployment workflows, TLS ingress, authenticated masking and storage
> adapters. See [current completion guide](completion-and-deployment.md). Hosted
> execution and external deployment have not been performed.

The inactive CI template at `ci-cd/member4-ci.yml` now defines two independent
security checks in addition to its existing tests:

| Check | Scope | Failure policy |
| --- | --- | --- |
| pip-audit matrix | Installed transport or federation environment, including transitive dependencies; audit tool isolated | Any reported vulnerability or incomplete dependency collection fails |
| Trivy image scan | OS and language packages in the built federation image | HIGH/CRITICAL findings fail, including those without available fixes |

Transport and federation install in separate jobs because their protobuf
requirements conflict. Federation installs CPU PyTorch before the package extra.
The editable local Member 4 package is excluded from advisory lookup because it
is unpublished; its third-party dependencies remain audited. This exclusion does
not constitute source-code security analysis.

`security/audit_requirements.py` exports all installed versions and maps only
`torch X+cpu` to upstream advisory version `X`, recording the mapping in a JSON
artifact. This checks upstream advisories, not CPU-wheel-specific vulnerabilities.
Unknown local-version suffixes fail rather than being silently excluded. The local
unpublished package is excluded, with its third-party dependencies retained.
No vulnerability ignore lists, automatic fixes or continue-on-error gates are used.

Reports are retained as GitHub artifacts for seven days when produced, including
after findings cause a failure. An install/build/network failure may prevent a
report from being created; the failed job remains the authoritative result.
Reports contain package information and findings, not application credentials.
The image is built locally in CI and is not pushed to a registry or deployed.

## Activation and first run

GitHub does not execute workflows stored under `infra/ci-cd/`. A team-owned change
must place the reviewed template in root `.github/workflows/`. That action remains
outside the user's infra-only change scope and has not been performed. After
activation, pull requests/pushes run the jobs and workflow_dispatch permits a
manual run. Configure required branch checks separately if the team wants merge
blocking; defining a failing job alone does not establish branch protection.

Review the first reports, update affected direct/transitive dependencies or base
images, run relevant compatibility checks, and scan again. Do not blindly upgrade
Flower/OR-Tools together or suppress a finding just to obtain a green run. If an
exception is justified, document the exact advisory, affected package, owner,
mitigation and expiry through the team's review process before changing policy.

Action references use version tags rather than immutable commit SHAs, and images
and transitive dependencies are not fully locked. Supply-chain pinning, monitoring
image scans (Prometheus/Grafana), secret scanning, IaC scanning and deployment
release gates remain pending. This step does not claim those controls exist.

## Validation performed

On September 30, local scans ran against both installed Python environments and
the built federation image. Initial pip-audit results: 34 advisories across six
federation packages and 12 in transport's pip. The initial Trivy image scan also
found HIGH/CRITICAL Debian and Python findings. Reports are in ignored
`outputs/security/`; a finding causes a nonzero exit as intended.

Compatible remediation upgrades Flower/PyTorch, cryptography within Flower's
supported range, protobuf, click and package tooling; the image applies available
Debian updates. Flower 1.39.0 requires cryptography below 47, while some reported
fixes require 48â€“50; do not override that dependency constraint and claim a supported
or clean installation. Debian findings without a fixed version remain unresolved.
Follow-up scan results must be reviewed before a production release.

Follow-up local dependency audit: transport reported zero known vulnerabilities;
federation reported seven advisory entries (four distinct IDs) in cryptography
46.0.7. The upstream CPU-PyTorch mapping limitation still applies. All 30 federation
checks passed after upgrades, and `pip check` reported no broken requirements.
Remaining cryptography advisories are blockers for real-data/production release,
not an approved security exception. Hosted CI remains inactive.

Tool references: [pip-audit](https://github.com/pypa/pip-audit),
[Trivy image scanning](https://trivy.dev/docs/latest/references/configuration/cli/trivy_image/)
and [Trivy GitHub Action](https://github.com/aquasecurity/trivy-action).

## Final targeted image scan

Pip-vendored msgpack/setuptools records were traced to `pip/_vendor/vendor.txt`
and `bom.cdx.json`. Runtime pip and its ensurepip wheel are now removed after
build-time dependency checks. Components were removed, not hidden from scanning;
container training still passed. Findings reduced from 49 to 47: 44 unfixed Debian
package/advisory occurrences and three cryptography findings beyond Flower's
supported range. See [exact findings](security-findings.md).
