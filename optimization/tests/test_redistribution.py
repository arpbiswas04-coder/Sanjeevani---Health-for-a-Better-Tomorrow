import copy
import itertools
import json
import random
import unittest
from pathlib import Path

from optimization.redistribution import ValidationError, recommend

EXAMPLES = Path(__file__).resolve().parents[1] / "redistribution" / "examples"


class RedistributionTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((EXAMPLES / "three_facilities.json").read_text())

    def test_fulfills_demand_at_expected_cost(self):
        result = recommend(self.request)
        self.assertEqual(result["status"], "fulfilled")
        self.assertEqual([t["quantity"] for t in result["recommended_transfers"]], [800, 400])
        self.assertEqual(result["estimated_transport_cost_paise"], 140000)
        self.assertEqual(result["unresolved_shortage"], 0)

    def test_partial_shortage(self):
        result = recommend(json.loads((EXAMPLES / "partial_shortage.json").read_text()))
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["unresolved_shortage"], 400)

    def test_cheapest_source_wins_over_nearest(self):
        self.request["candidate_sources"][1]["transport_cost_per_unit_paise"] = 50
        result = recommend(self.request)
        self.assertEqual(result["recommended_transfers"][0]["source"], "fac-12")

    def test_ties_are_deterministic(self):
        for source in self.request["candidate_sources"]:
            source["transport_cost_per_unit_paise"] = 100
            source["distance_km"] = 25
        first = recommend(self.request)["recommended_transfers"]
        self.request["candidate_sources"].reverse()
        self.assertEqual(first, recommend(self.request)["recommended_transfers"])

    def test_empty_sources_are_unavailable(self):
        self.request["candidate_sources"] = []
        result = recommend(self.request)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unresolved_shortage"], 1200)

    def test_zero_demand_creates_no_transfer(self):
        self.request["required_quantity"] = 0
        result = recommend(self.request)
        self.assertEqual(result["status"], "fulfilled")
        self.assertEqual(result["recommended_transfers"], [])

    def test_expired_and_near_expiry_sources_excluded(self):
        for expiry in (-1, 0, 6):
            with self.subTest(expiry=expiry):
                self.request["candidate_sources"][0]["expiry_days"] = expiry
                result = recommend(self.request, {"min_expiry_days": 7})
                self.assertEqual(result["fulfilled_quantity"], 700)
                self.assertIn("insufficient_remaining_shelf_life", result["excluded_sources"][0]["reasons"])

    def test_expiry_boundary_is_eligible(self):
        self.request["candidate_sources"][0]["expiry_days"] = 7
        self.assertEqual(recommend(self.request, {"min_expiry_days": 7})["status"], "fulfilled")

    def test_same_destination_and_zero_surplus_excluded(self):
        self.request["candidate_sources"][0]["facility_id"] = "fac-10"
        self.request["candidate_sources"][1]["safe_surplus"] = 0
        result = recommend(self.request)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(len(result["excluded_sources"]), 2)

    def test_invalid_quantities_rejected(self):
        for value in (-1, 1.5, True, "100", None):
            with self.subTest(value=value):
                self.request["required_quantity"] = value
                with self.assertRaises(ValidationError):
                    recommend(self.request)

    def test_invalid_candidate_fields_rejected(self):
        for field, values in {
            "safe_surplus": [-1, True, 2.5],
            "distance_km": [-1, True, float("nan"), float("inf"), 10**400],
            "transport_cost_per_unit_paise": [-1, True, 1.5],
            "expiry_days": [True, 1.5],
            "facility_id": ["", " leading", "x\ny"],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    request = copy.deepcopy(self.request)
                    request["candidate_sources"][0][field] = value
                    with self.assertRaises(ValidationError):
                        recommend(request)

    def test_duplicate_facility_cannot_double_count_surplus(self):
        self.request["candidate_sources"].append(copy.deepcopy(self.request["candidate_sources"][0]))
        with self.assertRaises(ValidationError):
            recommend(self.request)

    def test_unknown_and_missing_fields_rejected(self):
        for request in ({}, {**self.request, "transport_cost": 100}, []):
            with self.subTest(request_type=type(request).__name__):
                with self.assertRaises(ValidationError):
                    recommend(request)

    def test_policy_validation(self):
        for policy in ({"min_expiry_days": 0}, {"min_expiry_days": True}, {"typo": 7}, []):
            with self.subTest(policy=policy):
                with self.assertRaises(ValidationError):
                    recommend(self.request, policy)

    def test_no_input_mutation_and_approval_always_required(self):
        before = copy.deepcopy(self.request)
        result = recommend(self.request)
        self.assertEqual(self.request, before)
        self.assertTrue(result["recommendation_only"])
        self.assertTrue(result["approval_required"])
        self.assertEqual(result["inventory_snapshot_id"], before["inventory_snapshot_id"])

    def test_validates_all_sources_even_when_demand_is_zero(self):
        self.request["required_quantity"] = 0
        self.request["candidate_sources"][1]["safe_surplus"] = -1
        with self.assertRaises(ValidationError):
            recommend(self.request)

    def test_matches_exhaustive_optimum_for_small_random_cases(self):
        # Independent exhaustive oracle checks the optimization objective,
        # conservation of quantities, and source capacity over 100 scenarios.
        rng = random.Random(42)
        for _ in range(100):
            demand = rng.randrange(9)
            capacities = [rng.randrange(5) for _ in range(3)]
            costs = [rng.randrange(6) for _ in range(3)]
            request = copy.deepcopy(self.request)
            request["required_quantity"] = demand
            request["candidate_sources"] = [
                {"facility_id": f"source-{i}", "batch_id": f"batch-{i}",
                 "safe_surplus": capacity, "distance_km": i,
                 "expiry_days": 90, "transport_cost_per_unit_paise": cost}
                for i, (capacity, cost) in enumerate(zip(capacities, costs))
            ]
            possibilities = (
                (-sum(quantities), sum(q * c for q, c in zip(quantities, costs)))
                for quantities in itertools.product(*(range(c + 1) for c in capacities))
                if sum(quantities) <= demand
            )
            expected = min(possibilities)
            result = recommend(request)
            self.assertEqual((-result["fulfilled_quantity"], result["estimated_transport_cost_paise"]), expected)
            self.assertEqual(result["fulfilled_quantity"] + result["unresolved_shortage"], demand)
            for transfer in result["recommended_transfers"]:
                index = int(transfer["source"].split("-")[1])
                self.assertGreater(transfer["quantity"], 0)
                self.assertLessEqual(transfer["quantity"], capacities[index])


if __name__ == "__main__":
    unittest.main()

