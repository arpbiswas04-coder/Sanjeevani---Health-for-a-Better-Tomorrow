import copy
import importlib.util
import itertools
import json
import random
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from optimization.common.validation import ValidationError
from optimization.procurement import engine

EXAMPLE = Path(__file__).resolve().parents[1] / "procurement" / "example.json"
NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Install infra[transport]")
class ProcurementTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())

    def solve(self):
        return engine.recommend_procurement(self.request, now=NOW)

    def test_pack_cost_delivery_fee_and_no_mutation(self):
        original = copy.deepcopy(self.request)
        result = self.solve()
        self.assertEqual(result["purchased_quantity"], 30)
        self.assertEqual(result["total_cost_paise"], 350)
        self.assertEqual(result["overstock_units"], 5)
        self.assertEqual(result["recommended_orders"][0]["packs"], 3)
        self.assertEqual(result["solver_status"], "optimal")
        self.assertEqual(self.request, original)

    def test_budget_and_no_overstock_limits(self):
        self.request["budget_paise"] = 150
        result = self.solve()
        self.assertEqual(result["covered_quantity"], 10)
        self.assertEqual(result["unresolved_shortage"], 15)
        self.setUp()
        self.request["max_overstock_units"] = 0
        result = self.solve()
        self.assertEqual(result["purchased_quantity"], 25)
        self.assertEqual(result["total_cost_paise"], 390)

    def test_ineligible_quotes_and_zero_shortage(self):
        for field, value in (("approved", False), ("lead_time_days", 4), ("shelf_life_days_on_arrival", 0),
                             ("observed_at", "2026-09-30T11:00:00Z"), ("medicine_id", "other")):
            self.setUp()
            for offer in self.request["offers"]: offer[field] = value
            self.assertEqual(self.solve()["recommended_orders"], [])
        self.setUp()
        self.request["required_quantity"] = 0
        self.assertEqual(self.solve()["purchased_quantity"], 0)

    def test_invalid_types_duplicate_supplier_and_stale_snapshot(self):
        for case in ("boolean", "duplicate", "stale"):
            self.setUp()
            if case == "boolean": self.request["offers"][0]["pack_size"] = True
            elif case == "duplicate": self.request["offers"].append(copy.deepcopy(self.request["offers"][0]))
            else: self.request["captured_at"] = "2026-09-30T11:00:00Z"
            with self.assertRaises(ValidationError): self.solve()

    def test_timeout_does_not_invent_solution(self):
        from ortools.sat.python import cp_model as cp
        with patch.object(engine, "_solve", return_value=(cp.CpSolver(), cp.UNKNOWN)):
            result = self.solve()
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["unresolved_shortage"])
        self.assertEqual(result["recommended_orders"], [])
        original, calls = engine._solve, []
        def limited(module, model, seconds):
            calls.append(seconds)
            return original(module, model, seconds) if len(calls) == 1 else (cp.CpSolver(), cp.UNKNOWN)
        with patch.object(engine, "_solve", side_effect=limited):
            result = self.solve()
        self.assertEqual(result["covered_quantity"], 25)
        self.assertEqual(result["solver_status"], "feasible")
        self.assertEqual(result["proven_objectives"], ["maximize_shortage_coverage"])

    def test_zero_cost_does_not_encourage_unnecessary_overstock(self):
        for offer in self.request["offers"]:
            offer["price_per_pack_paise"] = offer["delivery_fee_paise"] = 0
        result = self.solve()
        self.assertEqual(result["purchased_quantity"], 25)
        self.assertEqual(result["total_cost_paise"], 0)

    def test_small_orders_match_exhaustive_optimum(self):
        rng = random.Random(304)
        for _ in range(20):
            self.setUp()
            demand, extra, budget = rng.randrange(9), rng.randrange(4), rng.randrange(30)
            self.request.update(required_quantity=demand, max_overstock_units=extra, budget_paise=budget)
            for offer in self.request["offers"]:
                offer.update(pack_size=rng.randrange(1, 5), available_packs=3, minimum_order_packs=rng.randrange(1, 4),
                             price_per_pack_paise=rng.randrange(8), delivery_fee_paise=rng.randrange(6))
            choices = []
            for counts in itertools.product(range(4), repeat=2):
                if any(n and n < offer["minimum_order_packs"] for n, offer in zip(counts, self.request["offers"])): continue
                quantity = sum(n * offer["pack_size"] for n, offer in zip(counts, self.request["offers"]))
                cost = sum(n * offer["price_per_pack_paise"] + (offer["delivery_fee_paise"] if n else 0)
                           for n, offer in zip(counts, self.request["offers"]))
                if quantity > demand + extra or cost > budget or (demand == 0 and quantity): continue
                choices.append((-min(demand, quantity), cost, quantity))
            result = self.solve()
            self.assertEqual((-result["covered_quantity"], result["total_cost_paise"], result["purchased_quantity"]), min(choices))
