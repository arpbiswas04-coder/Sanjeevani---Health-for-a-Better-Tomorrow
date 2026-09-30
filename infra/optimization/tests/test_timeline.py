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
