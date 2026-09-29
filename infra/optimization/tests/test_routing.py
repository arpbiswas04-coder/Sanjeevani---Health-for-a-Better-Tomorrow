import copy
import importlib.util
import itertools
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from optimization.common.validation import ValidationError
from optimization.routing import engine

EXAMPLE = Path(__file__).resolve().parents[1] / "routing" / "example.json"


@unittest.skipUnless(importlib.util.find_spec("ortools"), "Install infra[transport] to test routing")
class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())

    def solve(self, request=None):
        return engine.recommend_routes(self.request if request is None else request, time_limit_seconds=0.15)

    def assert_feasible(self, result, request):
        stop_map = {s["facility_id"]: s for s in request["stops"]}
        vehicle_map = {v["vehicle_id"]: v for v in request["vehicles"]}
        seen = []
        for route in result["routes"]:
            vehicle = vehicle_map[route["vehicle_id"]]
            self.assertLessEqual(route["quantity"], vehicle["capacity"])
            self.assertGreaterEqual(route["departure_minute"], max(vehicle["shift"][0], request["depot"]["window"][0]))
            self.assertLessEqual(route["return_minute"], min(vehicle["shift"][1], request["depot"]["window"][1]))
            self.assertEqual(route["duration_minutes"], route["travel_minutes"] + route["service_minutes"] + route["waiting_minutes"])
            self.assertEqual(route["legs"][0]["from"], request["depot"]["facility_id"])
            self.assertEqual(route["legs"][-1]["to"], request["depot"]["facility_id"])
            for visit in route["stops"]:
                stop = stop_map[visit["facility_id"]]
                seen.append(visit["facility_id"])
                self.assertEqual(visit["quantity"], stop["quantity"])
                self.assertGreaterEqual(visit["service_start_minute"], stop["window"][0])
                self.assertLessEqual(visit["service_end_minute"], stop["window"][1])
                self.assertGreaterEqual(visit["service_start_minute"], visit["earliest_arrival_minute"])
            for leg in route["legs"]:
                a, b = request["location_ids"].index(leg["from"]), request["location_ids"].index(leg["to"])
                self.assertEqual(leg["travel_minutes"], request["travel_time_minutes"][a][b])
                self.assertEqual(leg["distance_meters"], request["distance_meters"][a][b])
                self.assertGreaterEqual(leg["waiting_minutes"], 0)
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(set(seen) | {s["facility_id"] for s in result["unserved_stops"]}, set(stop_map))
        self.assertEqual(result["fulfilled_quantity"] + result["unresolved_quantity"], sum(s["quantity"] for s in request["stops"]))

    def test_demo_capacity_windows_return_and_no_mutation(self):
        before = copy.deepcopy(self.request)
        result = self.solve()
        self.assertEqual(result["fulfilled_quantity"], 15)
        self.assert_feasible(result, self.request)
        self.assertEqual(self.request, before)
        self.assertTrue(result["approval_required"])

    def test_capacity_shortage_leaves_whole_deliveries_unserved(self):
        self.request["vehicles"] = self.request["vehicles"][:1]
        self.request["vehicles"][0]["capacity"] = 10
        result = self.solve()
        self.assertEqual(result["fulfilled_quantity"], 10)
        self.assertEqual(result["status"], "partial")
        self.assert_feasible(result, self.request)

    def test_unreachable_window_and_oversized_delivery(self):
        self.request["stops"][0]["window"] = [0, 5]
        self.request["stops"][1]["quantity"] = 100
        result = self.solve()
        self.assertEqual({s["facility_id"] for s in result["unserved_stops"]}, {"phc-a", "phc-b"})
        self.assert_feasible(result, self.request)

    def test_waiting_and_late_vehicle_shift(self):
        for vehicle in self.request["vehicles"]:
            vehicle["shift"] = [30, 180]
        self.request["stops"][2]["window"] = [100, 120]
        result = self.solve()
        self.assertEqual(result["fulfilled_quantity"], 15)
        self.assert_feasible(result, self.request)

    def test_small_tour_matches_exhaustive_travel_optimum(self):
        self.request["vehicles"] = [{"vehicle_id": "van", "capacity": 20, "shift": [0, 180]}]
        for stop in self.request["stops"]:
            stop["window"] = [0, 180]
        matrix = self.request["travel_time_minutes"]
        optimum = min(sum(matrix[a][b] for a, b in zip((0,) + p, p + (0,)))
                      for p in itertools.permutations(range(1, 4)))
        result = self.solve()
        self.assertEqual(result["fulfilled_quantity"], 15)
        self.assertEqual(result["total_travel_minutes"], optimum)
        self.assert_feasible(result, self.request)

    def test_no_stops_and_all_dropped(self):
        for empty in (False, True):
            value = copy.deepcopy(self.request)
            if empty:
                value["stops"] = []
                value["location_ids"] = [value["depot"]["facility_id"]]
                value["travel_time_minutes"] = value["distance_meters"] = [[0]]
            else:
                for vehicle in value["vehicles"]:
                    vehicle["capacity"] = 1
            result = self.solve(value)
            self.assertTrue(result["has_solution"])
            self.assertEqual(result["routes"], [])
            self.assertEqual(result["status"], "fulfilled" if empty else "unavailable")

    def test_invalid_input_rejected(self):
        for case in ("order", "shape", "boolean", "negative", "duplicate", "shift", "service"):
            value = copy.deepcopy(self.request)
            if case == "order": value["location_ids"].reverse()
            elif case == "shape": value["travel_time_minutes"].pop()
            elif case == "boolean": value["vehicles"][0]["capacity"] = True
            elif case == "negative": value["distance_meters"][0][1] = -1
            elif case == "duplicate": value["stops"][0]["facility_id"] = "phc-b"
            elif case == "shift": value["vehicles"][0]["shift"] = [200, 300]
            else: value["stops"][0]["service_minutes"] = 100
            with self.subTest(case=case), self.assertRaises(ValidationError):
                self.solve(value)

    def test_no_incumbent_has_unknown_unserved_quantity(self):
        with patch.object(engine, "_solve", return_value=None):
            result = self.solve()
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["unresolved_quantity"])
        self.assertIsNone(result["unserved_stops"])
        self.assertFalse(result["optimality_proven"])
        self.assertEqual(result["status"], "not_computed")

    def test_cli(self):
        result = subprocess.run([sys.executable, "-m", "optimization.routing", "--input", str(EXAMPLE), "--time-limit", "0.15"],
                                cwd=EXAMPLE.parents[2], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["fulfilled_quantity"], 15)
