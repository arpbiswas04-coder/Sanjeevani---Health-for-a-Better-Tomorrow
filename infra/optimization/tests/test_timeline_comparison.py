import copy
import json
from pathlib import Path
import unittest
from optimization.simulation.comparison import compare_timelines
from optimization.common.validation import ValidationError


class TimelineComparisonTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1] / "simulation/comparison-example.json").read_text())

    def test_delay_deltas_replay_and_no_mutation(self):
        original = copy.deepcopy(self.data)
        result = compare_timelines(self.data)
        self.assertEqual(original, self.data)
        self.assertEqual(result, compare_timelines(self.data))
        self.assertEqual(result["baseline"]["summary"]["unmet_demand"], 400)
        scenario = result["scenarios"][0]
        self.assertEqual(scenario["delta_from_baseline"]["unmet_demand"], 500)
        self.assertEqual(scenario["delta_from_baseline"]["ending_safe_surplus"], 500)
        self.assertEqual(scenario["per_day_deltas"][1]["unmet_demand_delta"], 500)

    def test_zero_demand_and_incompatible_grid(self):
        for period in self.data["baseline_periods"]: period["demand"] = 0
        # Remove arrivals as the original batches now remain in stock.
        for period in self.data["baseline_periods"]: period.pop("arrivals", None)
        self.data["scenarios"][0]["periods"] = copy.deepcopy(self.data["baseline_periods"])
        result = compare_timelines(self.data)
        self.assertIsNone(result["baseline"]["summary"]["fulfillment_fraction"])
        self.assertIsNone(result["scenarios"][0]["delta_from_baseline"]["fulfillment_fraction"])
        self.data["scenarios"][0]["periods"][-1]["day"] = 3
        with self.assertRaises(ValidationError): compare_timelines(self.data)
