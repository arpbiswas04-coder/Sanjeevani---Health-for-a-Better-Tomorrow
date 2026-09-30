"""Optional end-to-end smoke check; skips in the lightweight environment."""

import importlib.util
import os
import unittest

from federated.regional import run_regional


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("flwr", "torch")),
                     "Optional federation environment required")
class RegionalSmokeTest(unittest.TestCase):
    def test_three_workers_train_and_evaluate_global_model(self):
        result = run_regional(rounds=1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["worker_failures"], [])
        self.assertEqual(result["coordinator"]["model_version"], 1)
        before = result["evaluations_before_rounds"][0]["regions"]
        final = result["final_evaluation"]
        self.assertTrue(final["complete"])
        self.assertEqual(len(before), 3)
        self.assertEqual(len({r["process_id"] for r in before}), 3)
        self.assertNotIn(os.getpid(), {r["process_id"] for r in before})
        self.assertEqual(len(final["regions"]), 3)
        for region in final["regions"]:
            self.assertEqual(region["evaluation_model_version"], 1)
            self.assertGreater(region["evaluation_samples"], 0)
        self.assertLess(sum(r["heldout_mse"] for r in final["regions"]),
                        sum(r["heldout_mse"] for r in before))
