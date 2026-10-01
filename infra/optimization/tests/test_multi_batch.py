import copy
import itertools
import random
import unittest

from optimization.redistribution import ValidationError
from optimization.redistribution.backend import recommend_all_batches
from optimization.tests.test_backend_adapter import NOW, row, snapshot


def multi_snapshot():
    value = snapshot()
    del value["sources"][0]["selected_batch_id"]
    return value


class MultiBatchTests(unittest.TestCase):
    def test_multiple_batches_fill_previously_unresolved_demand(self):
        value = multi_snapshot()
        value["required_quantity"] = 850
        value["sources"][0]["safety_stock"] = 0
        original = copy.deepcopy(value)
        result = recommend_all_batches(value, now=NOW)["data"]
        self.assertEqual([(t["batch_id"], t["quantity"]) for t in result["recommended_transfers"]],
                         [("batch-a", 700), ("batch-b", 150)])
        self.assertEqual(result["unresolved_shortage"], 0)
        self.assertEqual(result["estimated_transport_cost_paise"], 4250)
        self.assertEqual(result["schema_version"], "2.0")
        self.assertEqual(value, original)
        self.assertTrue(result["approval_required"])

    def test_shared_safety_cap_and_earliest_expiry(self):
        value = multi_snapshot()
        value["sources"][0]["inventory"][1]["batch"]["expires_on"] = "2026-10-15"
        result = recommend_all_batches(value, now=NOW)["data"]
        self.assertEqual([(t["batch_id"], t["quantity"]) for t in result["recommended_transfers"]],
                         [("batch-b", 200), ("batch-a", 400)])
        self.assertEqual(result["fulfilled_quantity"], 600)
        self.assertEqual(result["unresolved_shortage"], 400)
        self.assertEqual(result["surplus_calculations"][0]["safe_surplus"], 600)

    def test_recall_expiry_and_reservations_cannot_be_bypassed(self):
        for invalid in ({"recalled": True}, {"expires_on": "2026-09-30"}, {"medicine_id": "wrong"}):
            with self.subTest(invalid=invalid):
                value = multi_snapshot()
                value["sources"][0]["inventory"][1]["batch"].update(invalid)
                result = recommend_all_batches(value, now=NOW)["data"]
                self.assertEqual(result["fulfilled_quantity"], 400)
                self.assertEqual(len(result["recommended_transfers"]), 1)

    def test_empty_zero_and_safety_exhausted_results(self):
        for case in ("empty", "zero", "safety", "inactive", "destination"):
            with self.subTest(case=case):
                value = multi_snapshot()
                source = value["sources"][0]
                if case == "empty":
                    source["inventory"], source["reserved_quantities"] = [], {}
                elif case == "zero":
                    value["required_quantity"] = 0
                elif case == "safety":
                    source["safety_stock"] = 1000
                elif case == "inactive":
                    source["facility"]["active"] = False
                else:
                    value["destination"]["id"] = "source"
                result = recommend_all_batches(value, now=NOW)["data"]
                self.assertEqual(result["recommended_transfers"], [])
                self.assertNotIn("__facility_pool__", str(result))

    def test_ambiguous_v1_field_duplicate_facility_and_missing_reservations_rejected(self):
        for case in ("v1", "duplicate", "reservation", "stale"):
            value = multi_snapshot()
            if case == "v1":
                value["sources"][0]["selected_batch_id"] = "batch-a"
            elif case == "duplicate":
                value["sources"].append(copy.deepcopy(value["sources"][0]))
            elif case == "reservation":
                value["sources"][0]["reserved_quantities"] = {}
            else:
                value["captured_at"] = "2026-09-29T12:00:00Z"
            with self.assertRaises(ValidationError):
                recommend_all_batches(value, now=NOW)

    def test_reordering_rows_does_not_change_allocation(self):
        value = multi_snapshot()
        value["sources"][0]["safety_stock"] = 0
        expected = recommend_all_batches(value, now=NOW)["data"]["recommended_transfers"]
        value["sources"][0]["inventory"].reverse()
        self.assertEqual(recommend_all_batches(value, now=NOW)["data"]["recommended_transfers"], expected)

    def test_small_cases_match_exhaustive_group_capacity_optimum(self):
        rng = random.Random(81)
        for _ in range(60):
            value = multi_snapshot()
            demand = rng.randrange(9)
            capacities = [rng.randrange(4) for _ in range(4)]
            safeties = [rng.randrange(5) for _ in range(2)]
            costs = [rng.randrange(6) for _ in range(2)]
            value["required_quantity"] = demand
            value["sources"] = []
            for i in range(2):
                source = copy.deepcopy(multi_snapshot()["sources"][0])
                source["facility"]["id"] = f"source-{i}"
                source["safety_stock"] = safeties[i]
                source["transport_cost_per_unit_paise"] = costs[i]
                source["inventory"] = []
                source["reserved_quantities"] = {}
                for j in range(2):
                    k = 2 * i + j
                    item = row(f"row-{k}", f"batch-{k}", capacities[k])
                    item["facility_id"] = f"source-{i}"
                    source["inventory"].append(item)
                    source["reserved_quantities"][item["id"]] = 0
                value["sources"].append(source)
            limits = [max(0, sum(capacities[2*i:2*i+2]) - safeties[i]) for i in range(2)]
            feasible = [
                (-sum(q), sum(q[k] * costs[k // 2] for k in range(4)))
                for q in itertools.product(*(range(c + 1) for c in capacities))
                if sum(q) <= demand and sum(q[:2]) <= limits[0] and sum(q[2:]) <= limits[1]
            ]
            result = recommend_all_batches(value, now=NOW)["data"]
            self.assertEqual((-result["fulfilled_quantity"], result["estimated_transport_cost_paise"]), min(feasible))
            transfers = result["recommended_transfers"]
            self.assertEqual(sum(t["quantity"] for t in transfers), result["fulfilled_quantity"])
            self.assertEqual(sum(t["estimated_transport_cost_paise"] for t in transfers), result["estimated_transport_cost_paise"])
            self.assertEqual(result["fulfilled_quantity"] + result["unresolved_shortage"], demand)
            for i in range(2):
                self.assertLessEqual(sum(t["quantity"] for t in transfers if t["source"] == f"source-{i}"), limits[i])
            for transfer in transfers:
                self.assertLessEqual(transfer["quantity"], capacities[int(transfer["batch_id"].split("-")[1])])
