import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "optimization.redistribution", *args],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )

    def test_example_emits_json_and_logs_separately(self):
        result = self.run_cli("--input", "optimization/redistribution/examples/three_facilities.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["fulfilled_quantity"], 1200)
        self.assertIn("redistribution_completed", result.stderr)

    def test_partial_result_is_successful_computation(self):
        result = self.run_cli("--input", "optimization/redistribution/examples/partial_shortage.json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["unresolved_shortage"], 400)

    def test_healthcheck(self):
        result = self.run_cli("--healthcheck")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "ok")

    def test_missing_file(self):
        result = self.run_cli("--input", "nonexistent-test-input.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["error"], "invalid_request")

    def test_invalid_json_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for content in ('{', '{"x":1,"x":2}', '{"x":NaN}', '[]'):
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    result = self.run_cli("--input", str(path))
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(json.loads(result.stderr)["error"], "invalid_request")

    def test_policy_is_applied(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text('{"min_expiry_days":100}', encoding="utf-8")
            result = self.run_cli(
                "--input", "optimization/redistribution/examples/three_facilities.json",
                "--policy", str(path),
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["status"], "unavailable")

