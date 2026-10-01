import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock
from federated.privacy.gaussian import GaussianRelease
from federated.privacy.ledger import PrivacyLedger
from optimization.common.validation import ValidationError


class LedgerTests(unittest.TestCase):
    def test_restart_failure_charge_and_budget_refusal(self):
        policy = {"clipping_norm": 1, "noise_multiplier": 2, "delta": 1e-5, "max_epsilon": 3}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.sqlite"
            ledger = PrivacyLedger(path, policy, ['a','b','c'], initialize=True)
            accountant = GaussianRelease(policy, ledger=ledger, node='a')
            accountant._random = Mock()
            accountant._random.normalvariate.side_effect = RuntimeError('simulated sampling interruption')
            with self.assertRaises(RuntimeError): accountant.release([1, 0])
            restored = PrivacyLedger(path, policy, ['a','b','c'])
            self.assertEqual(restored.snapshot()['a'], 1)
            with self.assertRaises(ValidationError): GaussianRelease(policy, ledger=restored, node='a').release([1,0])
            with self.assertRaises(FileExistsError): PrivacyLedger(path, policy, ['a','b','c'], initialize=True)
            with self.assertRaises(ValidationError): PrivacyLedger(path, {**policy, 'noise_multiplier':4}, ['a','b','c'])
            with self.assertRaises(ValidationError): PrivacyLedger(path, policy, ['a','b','d'])
            with self.assertRaises(sqlite3.Error): PrivacyLedger(Path(directory)/'missing.sqlite', policy, ['a','b','c'])

    def test_stale_accountants_cannot_overdraw(self):
        policy = {"clipping_norm": 1, "noise_multiplier": 2, "delta": 1e-5, "max_epsilon": 3}
        with tempfile.TemporaryDirectory() as directory:
            ledger = PrivacyLedger(Path(directory)/'ledger.sqlite', policy, ['a','b','c'], initialize=True)
            first, second = [GaussianRelease(policy, ledger=ledger, node='a') for _ in range(2)]
            first.release([1,0])
            with self.assertRaises(ValidationError): second.release([1,0])
            self.assertEqual(ledger.snapshot()['a'], 1)
