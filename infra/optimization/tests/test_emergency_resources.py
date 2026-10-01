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
from optimization.emergency import resources
from optimization.transport import engine

EXAMPLE = Path(__file__).resolve().parents[1] / "emergency" / "resource-example.json"
NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Install infra[transport]")
class EmergencyResourceTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())

    def solve(self):
        return resources.recommend_emergency_resources(self.request, now=NOW)

    def test_priority_before_cost_and_no_mutation(self):
        before = copy.deepcopy(self.request)
        result = self.solve()
        allocation = result["allocation"]
        self.assertEqual(result["status"], "recommended")
        self.assertEqual([d["fulfilled_quantity"] for d in allocation["destinations"]], [8, 2])
        self.assertEqual(allocation["unresolved_shortage"], 6)
        self.assertEqual(allocation["estimated_transport_cost_paise"], 102)
        self.assertTrue(allocation["priority_optimal"])
        self.assertEqual(len(allocation["phases"]), 3)
        self.assertEqual(self.request, before)
        self.assertTrue(result["approval_required"])

    def test_hard_lane_and_expiry_limits(self):
        self.request["transport_request"]["lanes"][0]["capacity"] = 3
        self.assertEqual([d["fulfilled_quantity"] for d in self.solve()["allocation"]["destinations"]], [3, 7])
        self.request["transport_request"]["sources"][0]["batches"][0]["expiry_days"] = 0
        self.assertEqual(self.solve()["allocation"]["fulfilled_quantity"], 0)

    def test_missing_and_stale_scores_block_without_solving(self):
        for missing in (False, True):
            self.setUp()
            if missing: self.request["risk_request"]["facilities"].pop()
            else: self.request["risk_request"]["facilities"][1]["signals"]["bed_pressure"]["observed_at"] = "2026-09-30T11:00:00Z"
            with patch.object(resources, "recommend_transport") as solver:
                result = self.solve()
                solver.assert_not_called()
            self.assertEqual(result["status"], "needs_data_review")
            self.assertIsNone(result["allocation"])

    def test_scope_and_inventory_freshness(self):
        for case in ("request", "facility", "inventory"):
            self.setUp()
            if case == "request": self.request["risk_request"]["request_id"] = "other"
            elif case == "facility": self.request["risk_request"]["facilities"][0]["facility_id"] = "other"
            else: self.request["inventory_captured_at"] = "2026-09-30T11:55:00Z"
            with self.assertRaises(ValidationError): self.solve()

    def test_zero_scores_still_fulfill_demand_then_minimize_cost(self):
        for row in self.request["risk_request"]["facilities"]:
            for signal in row["signals"].values(): signal["value"] = 0
        allocation = self.solve()["allocation"]
        self.assertEqual(allocation["fulfilled_quantity"], 10)
        self.assertEqual([d["fulfilled_quantity"] for d in allocation["destinations"]], [2, 8])

    def test_priority_timeout_preserves_incumbent(self):
        from ortools.sat.python import cp_model as cp
        original, calls = engine._solve, []
        def solve(module, model, seconds):
            calls.append(seconds)
            return original(module, model, seconds) if len(calls) == 1 else (cp.CpSolver(), cp.UNKNOWN)
        with patch.object(engine, "_solve", side_effect=solve):
            result = self.solve()["allocation"]
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["fulfilled_quantity"], 10)
        self.assertTrue(result["fulfillment_optimal"])
        self.assertFalse(result["priority_optimal"])
        self.assertFalse(result["cost_optimal"])

    def test_expiry_during_computation_and_no_solution(self):
        with patch.object(resources, "utc_now", side_effect=[NOW, NOW + timedelta(minutes=6)]):
            result = resources.recommend_emergency_resources(self.request)
        self.assertEqual(result["status"], "expired_during_computation")
        from ortools.sat.python import cp_model as cp
        with patch.object(engine, "_solve", return_value=(cp.CpSolver(), cp.UNKNOWN)):
            result = self.solve()
        self.assertEqual(result["status"], "no_solution")
        self.assertIsNone(result["allocation"]["unresolved_shortage"])

    def test_priority_map_validation(self):
        for weights in ({"phc-high": 1}, {"phc-high": True, "phc-low": 1}, {"phc-high": 1000001, "phc-low": 1}):
            with self.assertRaises(ValidationError):
                engine.recommend_transport(self.request["transport_request"], priority_weights=weights)

    def test_small_cases_match_exhaustive_objectives(self):
        rng = random.Random(105)
        for _ in range(30):
            request = copy.deepcopy(self.request["transport_request"])
            capacity = rng.randrange(5)
            request["sources"][0]["safe_surplus"] = capacity
            weights = {"phc-high": rng.randrange(4), "phc-low": rng.randrange(4)}
            for lane in request["lanes"]:
                lane.update(capacity=rng.randrange(4), unit_cost_paise=rng.randrange(5), fixed_dispatch_cost_paise=rng.randrange(8))
            lanes = request["lanes"]
            choices = [(-sum(q), -sum(n * weights[lanes[i]["destination"]] for i, n in enumerate(q)),
                        sum(n * lanes[i]["unit_cost_paise"] + (lanes[i]["fixed_dispatch_cost_paise"] if n else 0)
                            for i, n in enumerate(q)))
                       for q in itertools.product(*(range(lane["capacity"] + 1) for lane in lanes)) if sum(q) <= capacity]
            result = engine.recommend_transport(request, priority_weights=weights)
            self.assertEqual((-result["fulfilled_quantity"], -result["priority_weighted_units"],
                              result["estimated_transport_cost_paise"]), min(choices))
            self.assertEqual(result["solver_status"], "optimal")

    def test_demo_cli(self):
        process = subprocess.run([sys.executable, "-m", "optimization.emergency", "--resources", "--demo"],
                                 cwd=EXAMPLE.parents[2], capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["allocation"]["fulfilled_quantity"], 10)
