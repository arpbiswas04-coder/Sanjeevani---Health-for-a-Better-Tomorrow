import importlib.util
import math
import unittest
from unittest.mock import Mock
from federated.privacy.gaussian import GaussianRelease
from optimization.common.validation import ValidationError


class GaussianTests(unittest.TestCase):
    def test_clipping_calibration_and_budget_cap(self):
        privacy = GaussianRelease({"clipping_norm": 1, "noise_multiplier": 2, "delta": 1e-5, "max_epsilon": 3})
        privacy._random = Mock()
        privacy._random.normalvariate.return_value = 0
        released = privacy.release([3, 4])
        self.assertAlmostEqual(released[0], .6)
        self.assertAlmostEqual(released[1], .8)
        privacy._random.normalvariate.assert_called_with(0, 4)
        self.assertAlmostEqual(privacy.budget()["epsilon"], .125 + 2*math.sqrt(.125*math.log(1e5)))
        with self.assertRaises(ValidationError): privacy.release([1, 1])
        self.assertEqual(privacy.releases, 1)


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "Optional federation environment required")
class SecureSumTests(unittest.TestCase):
    def test_masks_cancel_dropouts_replay_and_reuse_rejected(self):
        from federated.privacy.secure_sum import MaskingClient, aggregate
        clients = [MaskingClient(node) for node in ("a", "b", "c")]
        keys = {client.node: client.public for client in clients}
        values = [[.1, -.2], [.2, .3], [-.3, .5]]
        packets = [client.mask(value, keys, "round-one") for client, value in zip(clients, values)]
        result = aggregate(packets, keys, "round-one")
        self.assertAlmostEqual(result[0], 0)
        self.assertAlmostEqual(result[1], .2)
        for invalid, nonce in ((packets[:-1], "round-one"), (packets, "round-two"), ([packets[0]]*3, "round-one")):
            with self.assertRaises(ValidationError): aggregate(invalid, keys, nonce)
        with self.assertRaises(ValidationError): clients[0].mask(values[0], keys, "round-two")

    def test_combined_synthetic_demo(self):
        from federated.privacy.__main__ import run
        result = run(1)
        self.assertEqual(result["rounds"][0]["per_client_budget"]["releases"], 1)
        self.assertTrue(math.isfinite(result["rounds"][0]["private_public_grid_mse"]))
        self.assertFalse(result["production_private_training"])
