import copy
import importlib.util
import itertools
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from optimization.common.validation import ValidationError
from optimization.transport import engine

EXAMPLE = Path(__file__).resolve().parents[1] / "transport" / "example.json"


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Install infra[transport] to test CP-SAT")
class TransportTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())

    def test_fixed_cost_changes_cheapest_source(self):
        before = copy.deepcopy(self.request)
        result = engine.recommend_transport(self.request)
        self.assertEqual(result["solver_status"], "optimal")
        self.assertEqual(result["fulfilled_quantity"], 100)
        self.assertEqual(result["estimated_transport_cost_paise"], 420)
        self.assertEqual({t["source"] for t in result["recommended_transfers"]}, {"warehouse-b"})
        self.assertEqual(self.request, before)
        self.assertTrue(result["approval_required"])

    def test_shared_source_and_batch_capacity_across_destinations(self):
        self.request["lanes"] = self.request["lanes"][:2]
        self.request["sources"][0]["safe_surplus"] = 80
        result = engine.recommend_transport(self.request)
        self.assertEqual(result["fulfilled_quantity"], 80)
        self.assertEqual(result["unresolved_shortage"], 20)
        batches = {b: sum(t["quantity"] for t in result["recommended_transfers"] if t["batch_id"] == b)
                   for b in ("batch-a1", "batch-a2")}
        self.assertEqual(batches, {"batch-a1": 60, "batch-a2": 20})
        self.assertEqual(sum(d["total_cost_paise"] for d in result["dispatches"]), result["estimated_transport_cost_paise"])

    def test_lane_capacity_and_expiry_filtering(self):
        self.request["lanes"] = self.request["lanes"][:1]
        self.request["lanes"][0]["capacity"] = 25
        self.request["sources"][0]["batches"][0]["expiry_days"] = 0
        result = engine.recommend_transport(self.request)
        self.assertEqual(result["fulfilled_quantity"], 25)
        self.assertEqual(result["recommended_transfers"][0]["batch_id"], "batch-a2")
        self.assertEqual(len(result["excluded_batches"]), 1)

    def test_no_lanes_and_zero_demand_are_valid(self):
        for zero_demand in (False, True):
            value = copy.deepcopy(self.request)
            value["lanes"] = []
            if zero_demand:
                for destination in value["destinations"]:
                    destination["required_quantity"] = 0
            result = engine.recommend_transport(value)
            self.assertTrue(result["has_solution"])
            self.assertEqual(result["status"], "fulfilled" if zero_demand else "unavailable")
            self.assertEqual(result["dispatches"], [])
            self.assertEqual(result["estimated_transport_cost_paise"], 0)

    def test_invalid_contracts_fail_before_solving(self):
        for case in ("duplicate", "unknown", "boolean", "batch", "self", "negative"):
            value = copy.deepcopy(self.request)
            if case == "duplicate":
                value["lanes"].append(value["lanes"][0])
            elif case == "unknown":
                value["lanes"][0]["source"] = "missing"
            elif case == "boolean":
                value["lanes"][0]["capacity"] = True
            elif case == "batch":
                value["sources"][0]["batches"].append(value["sources"][0]["batches"][0])
            elif case == "self":
                value["destinations"][0]["facility_id"] = "warehouse-a"
            else:
                value["lanes"][0]["fixed_dispatch_cost_paise"] = -1
            with self.subTest(case=case), self.assertRaises(ValidationError):
                engine.recommend_transport(value)

    def test_invalid_time_limits(self):
        for limit in (0, -1, float("nan"), 61, True):
            with self.subTest(limit=limit), self.assertRaises(ValidationError):
                engine.recommend_transport(self.request, time_limit_seconds=limit)

    def test_no_incumbent_does_not_claim_shortage_or_solution(self):
        from ortools.sat.python import cp_model as cp
        with patch.object(engine, "_solve", return_value=(cp.CpSolver(), cp.UNKNOWN)):
            result = engine.recommend_transport(self.request)
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["unresolved_shortage"])
        self.assertIsNone(result["estimated_transport_cost_paise"])
        self.assertEqual(result["recommended_transfers"], [])
        self.assertEqual(result["status"], "not_computed")

    def test_cost_timeout_preserves_fulfillment_solution(self):
        from ortools.sat.python import cp_model as cp
        original = engine._solve
        calls = []

        def solve(module, model, seconds):
            calls.append(seconds)
            return original(module, model, seconds) if len(calls) == 1 else (cp.CpSolver(), cp.UNKNOWN)

        with patch.object(engine, "_solve", side_effect=solve):
            result = engine.recommend_transport(self.request)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["fulfilled_quantity"], 100)
        self.assertTrue(result["fulfillment_optimal"])
        self.assertFalse(result["cost_optimal"])
        self.assertEqual(result["solver_status"], "feasible")

    def test_unproven_fulfillment_skips_cost_optimization(self):
        from ortools.sat.python import cp_model as cp
        original = engine._solve

        def feasible(module, model, seconds):
            solver, _ = original(module, model, seconds)
            return solver, cp.FEASIBLE

        with patch.object(engine, "_solve", side_effect=feasible) as mocked:
            result = engine.recommend_transport(self.request)
        self.assertEqual(mocked.call_count, 1)
        self.assertFalse(result["fulfillment_optimal"])
        self.assertFalse(result["cost_optimal"])
        self.assertTrue(result["has_solution"])

    def test_random_small_allocations_match_exhaustive_fixed_cost_optimum(self):
        rng = random.Random(93)
        for _ in range(40):
            value = copy.deepcopy(self.request)
            capacities = [rng.randrange(4) for _ in range(2)]
            demands = [rng.randrange(4) for _ in range(2)]
            for i, source in enumerate(value["sources"]):
                source["safe_surplus"] = capacities[i]
            for i, destination in enumerate(value["destinations"]):
                destination["required_quantity"] = demands[i]
            for lane in value["lanes"]:
                lane.update(capacity=rng.randrange(3), unit_cost_paise=rng.randrange(5), fixed_dispatch_cost_paise=rng.randrange(9))
            lanes = value["lanes"]
            choices = [
                (-sum(q), sum(n * lanes[i]["unit_cost_paise"] + (lanes[i]["fixed_dispatch_cost_paise"] if n else 0)
                              for i, n in enumerate(q)))
                for q in itertools.product(*(range(lane["capacity"] + 1) for lane in lanes))
                if sum(q[:2]) <= capacities[0] and sum(q[2:]) <= capacities[1]
                and q[0] + q[2] <= demands[0] and q[1] + q[3] <= demands[1]
            ]
            result = engine.recommend_transport(value)
            self.assertEqual(result["solver_status"], "optimal")
            self.assertEqual((-result["fulfilled_quantity"], result["estimated_transport_cost_paise"]), min(choices))
            self.assertEqual(sum(t["quantity"] for t in result["recommended_transfers"]), result["fulfilled_quantity"])

    def test_cli_example(self):
        process = subprocess.run([sys.executable, "-m", "optimization.transport", "--input", str(EXAMPLE)],
                                 cwd=EXAMPLE.parents[2], capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["estimated_transport_cost_paise"], 420)
