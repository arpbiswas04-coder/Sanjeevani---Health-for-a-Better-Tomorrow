import json
from pathlib import Path
from datetime import datetime, timezone
import unittest
from optimization.simulation.forecast import simulate_forecast
from optimization.common.validation import ValidationError


class ForecastTests(unittest.TestCase):
    def test_valid_context_and_stale_or_mismatched_rejection(self):
        baseline = json.loads((Path(__file__).parents[1]/"simulation/example.json").read_text())["baseline"]
        now = datetime(2026, 9, 30, tzinfo=timezone.utc)
        forecast = {"forecast_id": "f-1", "model_version": "demand-v1", "generated_at": now.isoformat(),
                    "inventory_snapshot_id": baseline["inventory_snapshot_id"], "destination_id": baseline["shortage_facility"],
                    "medicine_id": baseline["medicine_id"], "quantity_unit": baseline["quantity_unit"],
                    "periods": [{"day": 0, "demand": 100}, {"day": 1, "demand": 200}]}
        result = simulate_forecast(baseline, forecast, now=now)
        self.assertEqual(result["totals"]["delivered"], 300)
        self.assertEqual(result["forecast_provenance"]["forecast_id"], "f-1")
        for field, value in (("medicine_id", "other"), ("quantity_unit", "box"), ("generated_at", "2020-01-01T00:00:00Z")):
            with self.assertRaises(ValidationError): simulate_forecast(baseline, {**forecast, field: value}, now=now)
