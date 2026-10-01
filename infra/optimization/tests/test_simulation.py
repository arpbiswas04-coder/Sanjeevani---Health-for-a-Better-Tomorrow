import copy
import json
from pathlib import Path
import unittest

from optimization.simulation import compare_scenarios
from optimization.common.validation import ValidationError


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1] / "simulation/example.json").read_text())

    def test_comparison_is_isolated_and_repeatable(self):
        original = copy.deepcopy(self.data)
        result = compare_scenarios(self.data)
        self.assertEqual(self.data, original)
        self.assertEqual(result, compare_scenarios(self.data))
        self.assertEqual(result["baseline"]["unresolved_shortage"], 0)
        demand, outage, expired = result["scenarios"]
        self.assertEqual(demand["delta_from_baseline"]["unresolved_shortage"], 300)
        self.assertEqual(outage["recommendation"]["fulfilled_quantity"], 700)
        self.assertEqual(expired["recommendation"]["fulfilled_quantity"], 800)

    def test_invalid_changes_are_rejected(self):
        for change in ({"facility_id": "unknown"}, {"facility_id": "fac-11", "lost_safe_surplus": 801},
                       {"facility_id": "fac-11", "unavailable": "yes"}):
            self.data["scenarios"] = [{"scenario_id": "invalid", "source_changes": [change]}]
            with self.assertRaises(ValidationError): compare_scenarios(self.data)
