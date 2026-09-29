import copy
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from optimization.common.validation import ValidationError
from optimization.emergency import score_emergency_priorities

DIRECTORY = Path(__file__).resolve().parents[1] / "emergency"
NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


class EmergencyTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((DIRECTORY / "example.json").read_text())
        self.policy = json.loads((DIRECTORY / "policy.example.json").read_text())

    def solve(self):
        return score_emergency_priorities(self.request, self.policy, now=NOW)

    def test_blueprint_weighted_score_and_no_mutation(self):
        before = copy.deepcopy(self.request)
        result = self.solve()
        row = result["ranked_facilities"][0]
        self.assertEqual(row["score"], 0.555)
        self.assertAlmostEqual(sum(c["contribution"] for c in row["components"]), row["score"])
        self.assertEqual(row["weight_coverage"], 1)
        self.assertEqual(self.request, before)
        self.assertTrue(result["approval_required"])
        self.assertIsNone(result["unscored_facilities"][0]["score"])

    def test_order_and_equal_scores_share_rank(self):
        first = self.request["facilities"][0]
        twin = copy.deepcopy(first)
        twin["facility_id"] = "phc-b"
        lower = copy.deepcopy(first)
        lower["facility_id"] = "phc-c"
        lower["signals"]["disease_growth"]["value"] = 0
        self.request["facilities"] = [lower, twin, first]
        rows = self.solve()["ranked_facilities"]
        self.assertEqual([r["facility_id"] for r in rows], ["phc-a", "phc-b", "phc-c"])
        self.assertEqual([r["rank"] for r in rows], [1, 1, 3])

    def test_missing_null_stale_and_future_are_unscored(self):
        for case in ("missing", "null", "stale", "future"):
            self.setUp()
            signals = self.request["facilities"][0]["signals"]
            if case == "missing": del signals["disease_growth"]
            elif case == "null": signals["disease_growth"]["value"] = None
            else: signals["disease_growth"]["observed_at"] = "2026-09-30T11:00:00Z" if case == "stale" else "2026-09-30T12:00:01Z"
            result = self.solve()
            self.assertEqual(result["scored_count"], 0)
            row = next(r for r in result["unscored_facilities"] if r["facility_id"] == "phc-a")
            self.assertIsNone(row["score"])
            self.assertEqual(row["weight_coverage"], 0.7)

    def test_zero_is_valid_and_missing_disabled_factor_does_not_block(self):
        for signal in self.request["facilities"][0]["signals"].values(): signal["value"] = 0
        self.assertEqual(self.solve()["ranked_facilities"][0]["score"], 0)
        self.policy["weights"]["disease_growth"] = 0
        self.policy["weights"]["resource_shortage"] = 0.55
        del self.request["facilities"][0]["signals"]["disease_growth"]
        self.assertEqual(self.solve()["scored_count"], 1)

    def test_weight_change_is_applied_and_version_recorded(self):
        self.policy["weights"]["disease_growth"] = 0.40
        self.policy["weights"]["resource_shortage"] = 0.15
        self.policy["policy_version"] = "experiment-2"
        result = self.solve()
        self.assertEqual(result["ranked_facilities"][0]["score"], 0.575)
        self.assertEqual(result["policy"]["policy_version"], "experiment-2")

    def test_expiry_tracks_oldest_active_signal(self):
        self.request["facilities"][0]["signals"]["bed_pressure"]["observed_at"] = "2026-09-30T11:30:00Z"
        self.assertEqual(self.solve()["ranked_facilities"][0]["valid_until"], "2026-09-30T12:30:00+00:00")

    def test_invalid_values_normalization_weights_and_duplicates_rejected(self):
        for value in (-0.1, 1.1, True, "0.5", float("nan")):
            self.setUp()
            self.request["facilities"][0]["signals"]["bed_pressure"]["value"] = value
            with self.assertRaises(ValidationError): self.solve()
        for case in ("weights", "normalization", "duplicate", "unknown"):
            self.setUp()
            if case == "weights": self.policy["weights"]["bed_pressure"] = 0.2
            elif case == "normalization": self.request["normalization_version"] = "different"
            elif case == "duplicate": self.request["facilities"].append(copy.deepcopy(self.request["facilities"][0]))
            else: self.request["facilities"][0]["signals"]["typo"] = None
            with self.assertRaises(ValidationError): self.solve()

    def test_invalid_snapshot_and_naive_signal_timestamp(self):
        for stamp in ("2026-09-30T11:00:00Z", "2026-09-30T12:00:01Z", "2026-09-30T12:00:00"):
            self.request["captured_at"] = stamp
            with self.assertRaises(ValidationError): self.solve()
        self.setUp()
        self.request["facilities"][0]["signals"]["bed_pressure"]["observed_at"] = "2026-09-30T12:00:00"
        with self.assertRaises(ValidationError): self.solve()

    def test_empty_and_all_missing_inputs(self):
        self.request["facilities"] = []
        self.assertEqual(self.solve()["scored_count"], 0)
        self.request["facilities"] = [{"facility_id": "x", "signals": {}}]
        row = self.solve()["unscored_facilities"][0]
        self.assertEqual(row["weight_coverage"], 0)
        self.assertEqual(len(row["issues"]), 6)

    def test_default_policy_and_demo_cli(self):
        self.assertEqual(score_emergency_priorities(self.request, now=NOW)["ranked_facilities"][0]["score"], 0.555)
        process = subprocess.run([sys.executable, "-m", "optimization.emergency", "--demo"],
                                 cwd=DIRECTORY.parents[1], capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["scored_count"], 1)
