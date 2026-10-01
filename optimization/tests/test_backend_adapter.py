import copy
import unittest
from datetime import datetime, timezone

from optimization.redistribution import ValidationError
from optimization.redistribution.backend import recommend_from_inventory

NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


def row(row_id, batch_id, quantity, expires_on="2026-12-01", recalled=False):
    return {"id": row_id, "facility_id": "source", "batch_id": batch_id,
            "quantity": quantity, "batch": {"id": batch_id, "medicine_id": "med",
            "expires_on": expires_on, "recalled": recalled}}


def snapshot():
    return {"request_id": "req", "inventory_snapshot_id": "snap",
            "captured_at": "2026-09-30T11:59:00Z",
            "destination": {"id": "destination", "active": True},
            "medicine": {"id": "med", "unit": "tablet"}, "required_quantity": 1000,
            "sources": [{"facility": {"id": "source", "active": True},
                "inventory_complete": True, "selected_batch_id": "batch-a",
                "safety_stock": 300, "reserved_quantities": {"row-a": 100, "row-b": 0},
                "distance_km": 10, "transport_cost_per_unit_paise": 5,
                "inventory": [row("row-a", "batch-a", 800), row("row-b", "batch-b", 200)]}]}


class BackendAdapterTests(unittest.TestCase):
    def test_maps_backend_records_and_preserves_safety_stock(self):
        value = snapshot()
        before = copy.deepcopy(value)
        result = recommend_from_inventory(value, now=NOW)
        self.assertTrue(result["success"])
        # (800 - 100 reserved) + 200 - 300 safety stock = 600 transferable.
        self.assertEqual(result["data"]["fulfilled_quantity"], 600)
        self.assertEqual(result["data"]["unresolved_shortage"], 400)
        self.assertEqual(result["data"]["quantity_unit"], "tablet")
        self.assertEqual(value, before)

    def test_selected_batch_capacity_limits_transfer(self):
        value = snapshot()
        value["sources"][0]["safety_stock"] = 0
        self.assertEqual(recommend_from_inventory(value, now=NOW)["data"]["fulfilled_quantity"], 700)

    def test_unusable_stock_does_not_support_safety_stock(self):
        for change in ({"recalled": True}, {"expires_on": "2026-09-30"}, {"medicine_id": "other"}):
            with self.subTest(change=change):
                value = snapshot()
                value["sources"][0]["inventory"][1]["batch"].update(change)
                data = recommend_from_inventory(value, now=NOW)["data"]
                self.assertEqual(data["fulfilled_quantity"], 400)
                self.assertEqual(len(data["snapshot_exclusions"]), 1)

    def test_recalled_selected_batch_and_inactive_source_never_transfer(self):
        for inactive in (False, True):
            value = snapshot()
            if inactive:
                value["sources"][0]["facility"]["active"] = False
            else:
                value["sources"][0]["inventory"][0]["batch"]["recalled"] = True
            self.assertEqual(recommend_from_inventory(value, now=NOW)["data"]["recommended_transfers"], [])

    def test_stale_future_and_naive_timestamps_rejected(self):
        for stamp in ("2026-09-30T11:00:00Z", "2026-09-30T12:01:00Z", "2026-09-30T12:00:00", "bad"):
            with self.subTest(stamp=stamp):
                value = snapshot()
                value["captured_at"] = stamp
                with self.assertRaises(ValidationError):
                    recommend_from_inventory(value, now=NOW)

    def test_partial_pages_missing_policy_and_bad_reservations_rejected(self):
        for changes in ({"inventory_complete": False}, {"safety_stock": None},
                        {"reserved_quantities": {}}, {"reserved_quantities": {"row-a": 801, "row-b": 0}},
                        {"reserved_quantities": {"row-a": 0, "row-b": 0, "extra": 0}}):
            with self.subTest(changes=changes):
                value = snapshot()
                value["sources"][0].update(changes)
                with self.assertRaises(ValidationError):
                    recommend_from_inventory(value, now=NOW)

    def test_wrong_facility_batch_reference_and_duplicate_rows_rejected(self):
        for field in ("facility_id", "batch_id", "duplicate"):
            value = snapshot()
            source = value["sources"][0]
            if field == "duplicate":
                source["inventory"].append(copy.deepcopy(source["inventory"][0]))
            else:
                source["inventory"][0][field] = "wrong"
            with self.assertRaises(ValidationError):
                recommend_from_inventory(value, now=NOW)

    def test_shelf_life_policy_and_midnight_rollover(self):
        value = snapshot()
        value["captured_at"] = "2026-09-29T23:59:00Z"
        value["sources"][0]["inventory"][0]["batch"]["expires_on"] = "2026-09-30"
        midnight = datetime(2026, 9, 30, 0, 1, tzinfo=timezone.utc)
        self.assertEqual(recommend_from_inventory(value, now=midnight)["data"]["fulfilled_quantity"], 0)
        value = snapshot()
        self.assertEqual(recommend_from_inventory(value, {"min_expiry_days": 100}, now=NOW)["data"]["fulfilled_quantity"], 0)

    def test_duplicate_source_cannot_reuse_surplus(self):
        value = snapshot()
        value["sources"].append(copy.deepcopy(value["sources"][0]))
        with self.assertRaises(ValidationError):
            recommend_from_inventory(value, now=NOW)

    def test_inactive_destination_and_missing_selected_batch_rejected(self):
        for case in ("inactive", "missing"):
            value = snapshot()
            if case == "inactive":
                value["destination"]["active"] = False
            else:
                value["sources"][0]["selected_batch_id"] = "missing"
            with self.assertRaises(ValidationError):
                recommend_from_inventory(value, now=NOW)
