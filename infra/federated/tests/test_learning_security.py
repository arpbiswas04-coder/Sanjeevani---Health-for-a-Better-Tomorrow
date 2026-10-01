import copy
import random
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from federated.privacy.authenticated import AuthenticatedRound, signed
from federated.privacy.secure_sum import MaskingClient
from federated.privacy.configuration import load, ConfiguredRelease
from federated.clients.client import SyntheticClient
from federated.clients.personalization import personalize
from optimization.common.validation import ValidationError


class LearningTests(unittest.TestCase):
    def setup_round(self):
        keys = {n: Ed25519PrivateKey.generate() for n in ('a', 'b', 'c')}
        public = {n: k.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw) for n, k in keys.items()}
        session = AuthenticatedRound(public, 2, 1)
        masks = {n: MaskingClient(n) for n in keys}
        announcements = [signed({**session.context, 'node_id': n, 'public_key': m.public.hex()}, keys[n]) for n, m in masks.items()]
        roster = session.establish(announcements)
        packets = [signed({**session.context, **m.mask([1, 2], roster, session.context['nonce'])}, keys[n]) for n, m in masks.items()]
        return session, packets, keys, announcements

    def test_aggregate_and_replay(self):
        session, packets, _, _ = self.setup_round()
        self.assertEqual(session.aggregate(packets), [1, 2])
        self.assertNotIn('samples', str(packets))
        self.assertNotIn('parameters', str(packets))
        with self.assertRaises(ValidationError): session.aggregate(packets)

    def test_invalid_rounds_participants_signatures_and_dropouts(self):
        for alteration in ('dropout', 'duplicate', 'unknown', 'round', 'model_version', 'signature', 'masked'):
            session, packets, keys, _ = self.setup_round()
            bad = copy.deepcopy(packets)
            if alteration == 'dropout': bad.pop()
            elif alteration == 'duplicate': bad[1] = bad[0]
            elif alteration == 'unknown': bad[0]['payload']['node_id'] = 'intruder'
            elif alteration == 'signature': bad[0]['signature'] = '00' * 64
            else:
                bad[0]['payload'][alteration] = [] if alteration == 'masked' else 999
                bad[0] = signed(bad[0]['payload'], keys['a'])
            with self.subTest(alteration=alteration), self.assertRaises(ValidationError):
                session.aggregate(bad)

    def test_peer_key_substitution_rejected(self):
        session, _, _, announcements = self.setup_round()
        announcements[0]['payload']['public_key'] = '00' * 32
        with self.assertRaises(ValidationError): session.verify(announcements[0], {'public_key'})

    def test_config_disabled_seeded_noise_and_validation(self):
        config = load(Path(__file__).parents[1] / 'configs/learning.json')['privacy']
        first, second = ConfiguredRelease(config), ConfiguredRelease(config)
        # Seed only in a unit test; production uses SystemRandom.
        first.mechanism._random = random.Random(5)
        second.mechanism._random = random.Random(5)
        self.assertEqual(first.release([.1, .2]), second.release([.1, .2]))
        self.assertEqual(ConfiguredRelease({**config, 'enabled': False}).release([3, 4]), [3, 4])
        for field, invalid in (('enabled', 'true'), ('noise_multiplier', 0), ('delta', 1), ('privacy_budget', -1)):
            with self.assertRaises(ValidationError): ConfiguredRelease({**config, field: invalid})

    def test_personalization_is_local_and_does_not_mutate_global(self):
        client = SyntheticClient('a', [(1, 3), (2, 5)])
        global_model = {'weight': 0., 'bias': 0.}
        config = {'enabled': False, 'local_epochs': 2, 'learning_rate': .01}
        self.assertEqual(personalize(client, global_model, config)['parameters'], global_model)
        result = personalize(client, global_model, {**config, 'enabled': True})
        self.assertNotEqual(result['parameters'], global_model)
        self.assertEqual(global_model, {'weight': 0., 'bias': 0.})
        self.assertEqual(set(result), {'scope', 'enabled', 'parameters'})
        with self.assertRaises(ValidationError): personalize(client, global_model, {**config, 'local_epochs': 0})
