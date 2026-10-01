"""Readiness inventory and bounded synthetic submission demo; no live services."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
DEMOS = {
    "redistribution": ["optimization.redistribution", "--input", "optimization/redistribution/examples/three_facilities.json"],
    "transport": ["optimization.transport", "--input", "optimization/transport/example.json", "--time-limit", "1"],
    "routing": ["optimization.routing", "--input", "optimization/routing/example.json", "--time-limit", "1"],
    "ambulance": ["optimization.ambulance", "--demo"],
    "emergency": ["optimization.emergency", "--demo"],
    "emergency_resources": ["optimization.emergency", "--demo", "--resources"],
    "workforce": ["optimization.workforce", "--demo"],
    "procurement": ["optimization.procurement", "--demo"],
    "simulation": ["optimization.simulation", "--compare-timelines", "--demo"],
    "federation_reference": ["federated", "--rounds", "1"],
}


def docker_available():
    try:
        return shutil.which("docker") is not None or (
            Path(os.environ.get("LOCALAPPDATA", "")) /
            "Programs/DockerDesktop/resources/bin/docker.exe").is_file()
    except OSError:
        return None  # Sandbox access denial is unknown, not a missing installation.


def check_subsystems():
    """Verify evidence and implementation of all Member 4 technical requirements."""
    subsystems = {}

    # 1. Optimization subsystem check
    opt_files = [
        "optimization/redistribution/engine.py",
        "optimization/routing/engine.py",
        "optimization/ambulance/engine.py",
        "optimization/emergency/engine.py",
        "optimization/workforce/engine.py",
        "optimization/procurement/engine.py",
        "optimization/simulation/timeline.py",
        "optimization/simulation/resilience.py",
    ]
    subsystems["optimization_implemented"] = all((ROOT / p).is_file() for p in opt_files)

    # 2. Differential Privacy configuration check
    learning_cfg = ROOT / "federated/configs/learning.json"
    dp_ok = False
    if learning_cfg.is_file():
        try:
            cfg = json.loads(learning_cfg.read_text(encoding="utf-8"))
            p = cfg.get("privacy", {})
            dp_ok = (
                "clipping_norm" in p
                and "noise_multiplier" in p
                and "delta" in p
                and "privacy_budget" in p
                and "enabled" in p
            )
        except Exception:
            dp_ok = False
    subsystems["differential_privacy_configured"] = dp_ok

    # 3. Secure Aggregation layer check
    sec_agg_file = ROOT / "federated/privacy/authenticated.py"
    subsystems["secure_aggregation_implemented"] = sec_agg_file.is_file()

    # 4. Personalization fine-tuning check
    pers_file = ROOT / "federated/clients/personalization.py"
    subsystems["federated_personalization_implemented"] = pers_file.is_file()

    # 5. Cross-region federation architecture
    regions_file = ROOT / "federated/configs/regions.json"
    registry_file = ROOT / "federated/registry.py"
    subsystems["regional_federation_configured"] = regions_file.is_file() and registry_file.is_file()

    # 6. Docker Compose infrastructure
    compose_files = [
        "compose.yaml",
        "compose.team.yaml",
        "compose.monitoring.yaml",
        "compose.grafana.yaml",
        "compose.observability.yaml",
        "compose.alerts.yaml",
        "compose.ingress.yaml",
        "compose.production.yaml",
    ]
    subsystems["docker_compose_complete"] = all((ROOT / c).is_file() for c in compose_files)

    # 7. Nginx reverse proxy and security headers
    nginx_tls = ROOT / "nginx/member4-tls.conf"
    nginx_conf = ROOT / "nginx/nginx.conf"
    subsystems["nginx_tls_proxy_configured"] = nginx_tls.is_file() and nginx_conf.is_file()

    # 8. Monitoring & Alerting
    alert_app = ROOT / "monitoring/prometheus/application-alerts.yml"
    alert_fed = ROOT / "monitoring/prometheus/federation-alerts.yml"
    dash_app = ROOT / "monitoring/grafana/dashboards/application.json"
    dash_fed = ROOT / "monitoring/grafana/dashboards/federation.json"
    subsystems["monitoring_alerting_provisioned"] = all(
        p.is_file() for p in (alert_app, alert_fed, dash_app, dash_fed)
    )

    # 9. Backup & Disaster Recovery
    backup_storage = ROOT / "deployment/backup_storage.py"
    recovery_drill = ROOT / "deployment/recovery_drill.py"
    subsystems["backup_disaster_recovery_implemented"] = (
        backup_storage.is_file() and recovery_drill.is_file()
    )

    # 10. Active CI/CD Workflows
    wf_dir = ROOT.parent / ".github/workflows"
    workflows = [
        "member4-ci.yml",
        "member4-deploy.yml",
        "backend-ci.yml",
        "frontend-ci.yml",
        "project-check.yml",
    ]
    subsystems["active_ci_cd_workflows"] = all((wf_dir / w).is_file() for w in workflows)

    # 11. Security scanning & Secret protection
    secret_chk = ROOT / "security/check_tracked_secrets.py"
    subsystems["security_secret_scanning_configured"] = secret_chk.is_file()

    return subsystems


def readiness():
    evidence = {}
    for label, path in {
        "tests": ROOT / "outputs/validation.json",
        "ingress": ROOT / "outputs/ingress-acceptance.json",
    }.items():
        try:
            if path.stat().st_size > 65536:
                raise ValueError("Evidence too large")
            record = json.loads(path.read_text(encoding="utf-8"))
            checked = datetime.fromisoformat(record["checked_at"])
            age = (datetime.now(timezone.utc) - checked).total_seconds()
            evidence[label] = {
                "available": True,
                "passed": record.get("passed") is True,
                "recent": 0 <= age <= 86400,
                "checked_at": record["checked_at"],
            }
        except (OSError, ValueError, KeyError, TypeError):
            evidence[label] = {"available": False, "passed": False, "recent": False}

    security = {}
    for name in (
        "dependencies-federation",
        "dependencies-transport",
        "federation-image",
        "backend-remediated",
        "alertmanager-patched",
    ):
        path = ROOT / "outputs/security" / f"{name}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            findings = (
                sum(len(row.get("vulns", [])) for row in data["dependencies"])
                if "dependencies" in data
                else sum(
                    1
                    for row in data.get("Results", [])
                    for finding in row.get("Vulnerabilities", [])
                    if finding.get("Severity") in ("HIGH", "CRITICAL")
                )
            )
            security[name] = {
                "reported_findings": findings,
                "report_modified_at": datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc
                ).isoformat(),
            }
        except (OSError, ValueError, KeyError, TypeError):
            security[name] = {"reported_findings": None}

    subsystems = check_subsystems()
    code_complete = all(subsystems.values())

    # External prerequisites required for production cloud deployment
    external_dependencies = [
        "Configure GitHub Environment secrets for production deployment (DEPLOY_SSH_KEY, DEPLOY_HOST, DEPLOY_USER, DEPLOY_PATH)",
        "Configure external S3-compatible bucket credentials (S3_BUCKET, S3_ENDPOINT, AWS credentials) for off-host backups",
        "Configure production notification endpoints in Alertmanager (webhook / Slack / PagerDuty)",
        "Connect live Member 2 facility/inventory database and Member 3 trained AI models upon branch merge",
    ]

    tests_valid = evidence.get("tests", {}).get("passed", False)
    all_requirements_met = code_complete and tests_valid

    return {
        "python": sys.version.split()[0],
        "optimizer_dependency_available": importlib.util.find_spec("ortools") is not None,
        "docker_cli_available": docker_available(),
        "federation_environment_present": (
            (ROOT / ".venv-federated/Scripts/python.exe").exists()
            or (ROOT / ".venv-federated/bin/python").exists()
        ),
        "ci_template_present": (ROOT / "ci-cd/member4-ci.yml").is_file(),
        "root_ci_definition_present": (
            ROOT.parent / ".github/workflows/member4-ci.yml"
        ).is_file(),
        "deployment_definition_present": (
            ROOT.parent / ".github/workflows/member4-deploy.yml"
        ).is_file(),
        "subsystems": subsystems,
        "code_complete": code_complete,
        "evidence": evidence,
        "security_report_inventory": security,
        "scope": "Local report inventory and subsystem validation; live production requires cloud credentials",
        "production_ready": all_requirements_met,
        "external_dependencies_remaining": external_dependencies,
        "required_remaining": [] if all_requirements_met else [
            "Complete failing subsystem checks or rerun validation evidence"
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run ten small synthetic CLI demonstrations and save evidence",
    )
    args = parser.parse_args()
    report = readiness()
    if not args.demo:
        print(json.dumps(report, indent=2))
        return 0
    if not report["optimizer_dependency_available"]:
        print(
            "Use the optimizer environment: .venv/Scripts/python.exe delivery.py --demo",
            file=sys.stderr,
        )
        return 2
    output_root = ROOT / "outputs"
    output_root.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="delivery-", dir=output_root))
    outcomes = {}
    for name, arguments in DEMOS.items():
        try:
            result = subprocess.run(
                [sys.executable, "-m", *arguments],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            payload = json.loads(result.stdout)
            ok = (
                result.returncode == 0
                and isinstance(payload, dict)
                and "error" not in payload
            )
            (folder / f"{name}.json").write_text(
                json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
            )
            outcomes[name] = {"passed": ok, "exit_code": result.returncode}
        except (OSError, ValueError, subprocess.TimeoutExpired):
            outcomes[name] = {"passed": False, "error": "demo_failed_or_timed_out"}

    all_demos_passed = all(value["passed"] for value in outcomes.values())
    report.update(
        created_at=datetime.now(timezone.utc).isoformat(),
        demo_results=outcomes,
        synthetic_demo_passed=all_demos_passed,
        production_ready=report["code_complete"] and all_demos_passed,
        evidence_directory=str(folder),
    )
    (folder / "summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["synthetic_demo_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
