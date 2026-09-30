# Member 4 dependency and image scanning

The inactive CI template at `ci-cd/member4-ci.yml` now defines two independent
security checks in addition to its existing tests:

| Check | Scope | Failure policy |
| --- | --- | --- |
| pip-audit matrix | Installed transport or federation environment, including transitive and audit-tool dependencies | Any reported vulnerability or incomplete dependency collection fails |
| Trivy image scan | OS and language packages in the built federation image | HIGH/CRITICAL findings fail, including those without available fixes |

Transport and federation install in separate jobs because their protobuf
requirements conflict. Federation installs CPU PyTorch before the package extra.
The editable local Member 4 package is excluded from advisory lookup because it
is unpublished; its third-party dependencies remain audited. This exclusion does
not constitute source-code security analysis.

The strict audit may fail when a distribution such as a CPU-specific PyTorch
build cannot be matched to the advisory service. Treat that as incomplete coverage,
not a clean result. Inspect the report/log and resolve package identification
before declaring the audit passed. There are no vulnerability ignore lists,
automatic fixes, or continue-on-error gates in this template.

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

Only workflow YAML structure and the security job settings were checked locally.
No scanner was installed/run, advisory database downloaded, image built or tests
rerun. Consequently there is **no vulnerability-free assessment** yet. Docker is
also unavailable on this host.

Tool references: [pip-audit](https://github.com/pypa/pip-audit),
[Trivy image scanning](https://trivy.dev/docs/latest/references/configuration/cli/trivy_image/)
and [Trivy GitHub Action](https://github.com/aquasecurity/trivy-action).
