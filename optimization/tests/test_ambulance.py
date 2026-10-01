import copy
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from optimization.ambulance import recommend_ambulance
from optimization.common.validation import ValidationError

EXAMPLE = Path(__file__).resolve().parents[1] / "ambulance" / "example.json"
NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


class AmbulanceTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())

    def solve(self, policy=None):
        return recommend_ambulance(self.request, policy, now=NOW)

    def test_eligibility_before_eta_and_no_mutation(self):
        before = copy.deepcopy(self.request)
        result = self.solve()
        self.assertEqual(result["recommended"]["ambulance_id"], "amb-a")
        self.assertEqual(result["alternatives"][0]["ambulance_id"], "amb-b")
        self.assertEqual(set(result["rejected_candidates"][0]["reasons"]),
                         {"not_available", "already_reserved", "missing_required_equipment"})
        self.assertEqual(self.request, before)
        self.assertTrue(result["approval_required"])

    def test_each_hard_constraint_blocks_fast_candidate(self):
        for field, value in {"status": "maintenance", "reserved": True, "crew_ready": False,
                             "serviceable": False, "equipment": [], "supported_emergency_types": [],
                             "eta_minutes": None}.items():
            with self.subTest(field=field):
                self.setUp()
                self.request["candidates"][0][field] = value
                self.assertEqual(self.solve()["recommended"]["ambulance_id"], "amb-b")

    def test_patient_capacity_and_no_candidate_case(self):
        self.request["patient_count"] = 2
        self.assertEqual(self.solve()["status"], "no_eligible_ambulance")
        self.request["candidates"] = []
        result = self.solve()
        self.assertIsNone(result["recommended"])
        self.assertEqual(result["alternatives"], [])

    def test_stale_future_and_naive_snapshot_rejected(self):
        for stamp in ("2026-09-30T11:58:00Z", "2026-09-30T12:01:00Z", "2026-09-30T12:00:00"):
            self.request["captured_at"] = stamp
            with self.assertRaises(ValidationError): self.solve()

    def test_stale_candidate_or_eta_excluded_and_expiry_tracks_oldest(self):
        self.request["candidates"][0]["observed_at"] = "2026-09-30T11:58:00Z"
        self.assertEqual(self.solve()["recommended"]["ambulance_id"], "amb-b")
        self.setUp()
        self.request["candidates"][0]["eta_observed_at"] = "2026-09-30T11:59:00Z"
        self.assertEqual(self.solve()["valid_until"], "2026-09-30T12:01:00+00:00")
        self.request["candidates"][0]["eta_observed_at"] = "2026-09-30T12:00:01Z"
        self.assertEqual(self.solve()["recommended"]["ambulance_id"], "amb-b")

    def test_eta_threshold_and_alternative_limit(self):
        result = self.solve({"max_eta_minutes": 10, "max_alternatives": 0})
        self.assertEqual(result["eligible_count"], 1)
        self.assertEqual(result["alternatives"], [])
        self.assertEqual(self.solve({"max_alternatives": 0})["alternatives_omitted"], 1)

    def test_deterministic_ties_and_optional_distance(self):
        for candidate in self.request["candidates"][:2]:
            candidate["eta_minutes"] = 10
            candidate["distance_km"] = None
        self.request["candidates"].reverse()
        self.assertEqual(self.solve()["recommended"]["ambulance_id"], "amb-a")
        self.request["candidates"][1]["distance_km"] = 4
        self.assertEqual(self.solve()["recommended"]["ambulance_id"], "amb-b")

    def test_bad_types_duplicates_and_policy_fail(self):
        for field, value in {"reserved": "false", "patient_capacity": True, "eta_minutes": float("nan"),
                             "equipment": ["x", "x"], "distance_km": -1}.items():
            self.setUp()
            self.request["candidates"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError): self.solve()
        self.setUp()
        self.request["candidates"].append(copy.deepcopy(self.request["candidates"][0]))
        with self.assertRaises(ValidationError): self.solve()
        self.setUp()
        for policy in ({"max_age_seconds": 0}, {"max_alternatives": 21}, {"max_eta_minutes": True}):
            with self.assertRaises(ValidationError): self.solve(policy)

    def test_demo_cli(self):
        process = subprocess.run([sys.executable, "-m", "optimization.ambulance", "--demo"],
                                 cwd=EXAMPLE.parents[2], capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["recommended"]["ambulance_id"], "amb-a")
