import copy
import importlib.util
import itertools
import json
import random
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from optimization.common.validation import ValidationError
from optimization.workforce import engine

EXAMPLE = Path(__file__).resolve().parents[1] / "workforce" / "example.json"
NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Install infra[transport]")
class WorkforceTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())

    def solve(self):
        return engine.recommend_staff(self.request, now=NOW)

    def test_qualified_matching_and_no_mutation(self):
        before = copy.deepcopy(self.request)
        result = self.solve()
        self.assertEqual({a["worker_id"]: a["destination"] for a in result["assignments"]},
                         {"worker-a": "phc-special", "worker-b": "phc-general"})
        self.assertEqual(result["total_travel_minutes"], 60)
        self.assertEqual(result["source_staffing"][0]["remaining_staff"], 1)
        self.assertEqual(self.request, before)
        self.assertTrue(result["approval_required"])

    def test_shared_staffing_floor_and_existing_deficit(self):
        for minimum, expected in ((2, 1), (3, 0), (4, 0)):
            self.request["staffing"][0]["minimum_required"] = minimum
            result = self.solve()
            self.assertEqual(result["assigned_staff"], expected)
            self.assertEqual(result["source_staffing"][0]["remaining_staff"], 3 - expected)

    def test_worker_gates_and_reservations(self):
        for field, value in (("reserved", True), ("available", False), ("transferable", False), ("rest_ready", False)):
            self.setUp()
            self.request["workers"][0][field] = value
            self.assertEqual([a["worker_id"] for a in self.solve()["assignments"]], ["worker-b"])

    def test_travel_before_and_after_shift_must_fit(self):
        for field, value in (("available_from", "2026-09-30T13:00:00Z"), ("available_until", "2026-09-30T21:00:00Z")):
            self.setUp()
            self.request["workers"][0][field] = value
            self.assertEqual(self.solve()["assigned_staff"], 1)

    def test_absent_lane_and_no_cross_role_substitution(self):
        self.request["lanes"] = []
        self.assertEqual(self.solve()["assigned_staff"], 0)
        self.setUp()
        self.request["demands"][0]["role"] = "different-role"
        self.assertEqual(self.solve()["assigned_staff"], 1)

    def test_stale_snapshot_worker_and_bad_roster(self):
        self.request["captured_at"] = "2026-09-30T11:55:00Z"
        with self.assertRaises(ValidationError): self.solve()
        self.setUp()
        self.request["workers"][0]["observed_at"] = "2026-09-30T11:55:00Z"
        self.assertEqual(self.solve()["assigned_staff"], 1)
        self.setUp()
        self.request["staffing"][0]["on_duty"] = 1
        with self.assertRaises(ValidationError): self.solve()
        self.setUp()
        self.request["workers"].append(copy.deepcopy(self.request["workers"][0]))
        with self.assertRaises(ValidationError): self.solve()

    def test_no_incumbent_and_expiry_are_not_dispatchable(self):
        from ortools.sat.python import cp_model as cp
        with patch.object(engine, "_solve", return_value=(cp.CpSolver(), cp.UNKNOWN)):
            result = self.solve()
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["shortages"][0]["unresolved_staff"])
        with patch.object(engine, "utc_now", side_effect=[NOW, NOW + timedelta(minutes=6)]):
            result = engine.recommend_staff(self.request)
        self.assertEqual(result["status"], "expired_during_computation")

    def test_small_matching_cases_against_exhaustive_oracle(self):
        rng = random.Random(202)
        for _ in range(25):
            self.setUp()
            minimum = rng.randrange(4)
            self.request["staffing"][0]["minimum_required"] = minimum
            for worker in self.request["workers"]:
                worker["skills"] = [skill for skill in ("basic", "special") if rng.choice((True, False))]
            for lane in self.request["lanes"]:
                lane["outbound_minutes"] = lane["return_minutes"] = rng.randrange(1, 25)
            choices = []
            for targets in itertools.product((-1, 0, 1), repeat=2):
                used = [t for t in targets if t >= 0]
                if len(used) > max(0, 3 - minimum) or len(set(used)) != len(used): continue
                if any(t >= 0 and not set(self.request["demands"][t]["required_skills"]).issubset(self.request["workers"][i]["skills"])
                       for i, t in enumerate(targets)): continue
                cost = sum(self.request["lanes"][t]["outbound_minutes"] + self.request["lanes"][t]["return_minutes"] for t in used)
                choices.append((-len(used), cost))
            result = self.solve()
            self.assertEqual((-result["assigned_staff"], result["total_travel_minutes"]), min(choices))
            self.assertEqual(len({a["worker_id"] for a in result["assignments"]}), len(result["assignments"]))

    def test_demo_cli(self):
        process = subprocess.run([sys.executable, "-m", "optimization.workforce", "--demo"],
                                 cwd=EXAMPLE.parents[2], capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["assigned_staff"], 2)
