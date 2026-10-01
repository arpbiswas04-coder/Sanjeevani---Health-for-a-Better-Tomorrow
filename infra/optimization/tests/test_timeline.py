import copy
import json
from pathlib import Path
import unittest
from optimization.simulation.timeline import run_timeline
from optimization.common.validation import ValidationError


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1] / "simulation/timeline-example.json").read_text())

    def test_stock_conservation_blocking_expiry_and_replay(self):
        original = copy.deepcopy(self.data)
        result = run_timeline(self.data)
        self.assertEqual(self.data, original)
        self.assertEqual(result, run_timeline(self.data))
        first, second, third = result["periods"]
        self.assertEqual(first["closing_safe_surplus"], {"fac-11": 300, "fac-12": 700})
        self.assertEqual(second["closing_safe_surplus"], {"fac-11": 200, "fac-12": 100})
        self.assertEqual(third["expired"], {"fac-12": 100})
        self.assertEqual(result["totals"]["delivered"], 1300)
        self.assertEqual(result["totals"]["unmet_demand"], 300)
        self.assertEqual(result["initial_safe_surplus"], sum(result["final_safe_surplus"].values()) + sum(result["totals"][key] for key in ("delivered", "lost", "expired")))

    def test_invalid_day_and_loss(self):
        self.data["periods"][1]["day"] = 0
        with self.assertRaises(ValidationError): run_timeline(self.data)
        self.data["periods"][1]["day"] = 1
        self.data["periods"][1]["losses"][0]["quantity"] = 301
        with self.assertRaises(ValidationError): run_timeline(self.data)

    def test_arrivals_and_supplier_delay(self):
        receipt = {"facility_id": "fac-11", "batch_id": "new-batch", "safe_surplus": 500, "expiry_days": 5}
        self.data["periods"] = [{"day": 0, "demand": 1500}, {"day": 1, "demand": 900, "arrivals": [receipt]}, {"day": 2, "demand": 0}]
        timely = run_timeline(self.data)
        self.assertEqual(timely["totals"]["unmet_demand"], 400)
        self.data["periods"][1].pop("arrivals")
        self.data["periods"][2]["arrivals"] = [receipt]
        delayed = run_timeline(self.data)
        self.assertEqual(delayed["totals"]["unmet_demand"], 900)
        self.assertEqual(delayed["final_safe_surplus"]["fac-11"], 500)
        self.assertEqual(delayed["initial_safe_surplus"] + delayed["totals"]["arrived"], sum(delayed["final_safe_surplus"].values()) + sum(delayed["totals"][key] for key in ("delivered", "lost", "expired")))

    def test_blocked_arrival_then_expiry(self):
        receipt = {"facility_id": "fac-11", "batch_id": "new-batch", "safe_surplus": 500, "expiry_days": 2}
        self.data["periods"] = [{"day": 0, "demand": 1500}, {"day": 1, "demand": 100, "arrivals": [receipt], "blocked_sources": ["fac-11"]}, {"day": 3, "demand": 100}]
        result = run_timeline(self.data)
        self.assertEqual(result["periods"][1]["closing_safe_surplus"]["fac-11"], 500)
        self.assertEqual(result["periods"][2]["expired"]["fac-11"], 500)

    def test_arrivals_cannot_merge_batches_or_reset_expiry(self):
        for batch, expiry in (("new-batch", 90), ("batch-11-a", 100)):
            self.data["periods"] = [{"day": 0, "demand": 0, "arrivals": [{"facility_id": "fac-11", "batch_id": batch, "safe_surplus": 100, "expiry_days": expiry}]}]
            with self.assertRaises(ValidationError): run_timeline(self.data)
