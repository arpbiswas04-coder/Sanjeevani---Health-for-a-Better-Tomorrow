"""Readiness inventory and bounded synthetic submission demo; no live services."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
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


def readiness():
    return {"python": sys.version.split()[0],
            "optimizer_dependency_available": importlib.util.find_spec("ortools") is not None,
            "docker_cli_available": shutil.which("docker") is not None,
            "federation_environment_present": (ROOT / ".venv-federated/Scripts/python.exe").exists() or (ROOT / ".venv-federated/bin/python").exists(),
            "ci_template_present": (ROOT / "ci-cd/member4-ci.yml").is_file(),
            "scope": "Local prerequisite inventory only; does not verify Docker daemon, credentials or deployed services",
            "required_remaining": ["Integrate and audit reference privacy mechanisms for real training",
                                   "Authenticated secure aggregation with dropout/collusion handling",
                                   "Member 2 live APIs/approval integration and Member 3 model/data integration",
                                   "Full application Docker deployment and runtime verification",
                                   "Activate and execute reviewed CI/security checks",
                                   "Execute PostgreSQL restore drill; add object-storage/off-host recovery"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run ten small synthetic CLI demonstrations and save evidence")
    args = parser.parse_args()
    report = readiness()
    if not args.demo:
        print(json.dumps(report, indent=2))
        return 0
    if not report["optimizer_dependency_available"]:
        print("Use the optimizer environment: .venv/Scripts/python.exe delivery.py --demo", file=sys.stderr)
        return 2
    output_root = ROOT / "outputs"
    output_root.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="delivery-", dir=output_root))
    outcomes = {}
    for name, arguments in DEMOS.items():
        try:
            result = subprocess.run([sys.executable, "-m", *arguments], cwd=ROOT,
                                    capture_output=True, text=True, timeout=30)
            payload = json.loads(result.stdout)
            ok = result.returncode == 0 and isinstance(payload, dict) and "error" not in payload
            (folder / f"{name}.json").write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
            outcomes[name] = {"passed": ok, "exit_code": result.returncode}
        except (OSError, ValueError, subprocess.TimeoutExpired):
            outcomes[name] = {"passed": False, "error": "demo_failed_or_timed_out"}
    report.update(created_at=datetime.now(timezone.utc).isoformat(), demo_results=outcomes,
                  synthetic_demo_passed=all(value["passed"] for value in outcomes.values()),
                  production_ready=False, evidence_directory=str(folder))
    (folder / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["synthetic_demo_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
