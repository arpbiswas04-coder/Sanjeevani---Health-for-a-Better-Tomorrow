"""Automated verification of Member 4 test suites and evidence generation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Ensure infra is in sys.path
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_suite(start_dir):
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(start_dir))
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=1)
    result = runner.run(suite)
    return {
        "tests_run": result.testsRun,
        "errors": len(result.errors),
        "failures": len(result.failures),
        "skipped": len(result.skipped),
        "passed": result.wasSuccessful(),
    }


def main():
    print("Running Member 4 comprehensive test verification...")
    results = {}

    opt_dir = ROOT / "optimization/tests"
    fed_dir = ROOT / "federated/tests"
    mon_dir = ROOT / "monitoring/tests"

    if opt_dir.is_dir():
        print("\n--- Optimization Tests ---")
        results["optimization"] = run_suite(opt_dir)

    if fed_dir.is_dir():
        print("\n--- Federated Learning Tests ---")
        results["federation"] = run_suite(fed_dir)

    if mon_dir.is_dir():
        print("\n--- Monitoring & Operations Tests ---")
        results["monitoring"] = run_suite(mon_dir)

    all_passed = all(r.get("passed", False) for r in results.values())
    total_tests = sum(r.get("tests_run", 0) for r in results.values())
    total_failures = sum(r.get("failures", 0) + r.get("errors", 0) for r in results.values())

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "passed": all_passed,
        "total_tests": total_tests,
        "total_failures": total_failures,
        "suites": results,
        "scope": "Comprehensive Member 4 local test execution and verification",
    }

    output_path = ROOT / "outputs/validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved validation evidence to {output_path}")
    print(f"Total tests: {total_tests}, All passed: {all_passed}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
