"""Signed fixed-roster masking protocol. Pinned identities are supplied out of band.

Fresh session nonce binds round/model and ephemeral keys. All clients must agree
on the same signed roster. Dropout aborts; no malicious-client/collusion guarantee.
"""
import json
import logging
import secrets
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from federated.privacy.secure_sum import aggregate, transcript
from optimization.common.validation import ValidationError, integer, identifier, object_fields

LOGGER = logging.getLogger(__name__)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def signed(value, private_key):
    return {'payload': value, 'signature': private_key.sign(canonical(value)).hex()}


class AuthenticatedRound:
    def __init__(self, identities, round_id, model_version, *, nonce=None):
        if not isinstance(identities, dict) or not 3 <= len(identities) <= 100:
            raise ValidationError('Require 3..100 pinned participant identities')
        self.identities = {}
        for node, key in identities.items():
            identifier(node, 'node')
            if not isinstance(key, bytes) or len(key) != 32:
                raise ValidationError('Invalid pinned identity')
            self.identities[node] = Ed25519PublicKey.from_public_bytes(key)
        if len(set(identities.values())) != len(identities):
            raise ValidationError('Each node needs a distinct identity')
        self.context = {'protocol': 'authenticated-masked-v1',
                        'round': integer(round_id, 'round', 1),
                        'model_version': integer(model_version, 'model_version'),
                        'nonce': identifier(nonce or secrets.token_hex(32), 'nonce')}
        self.keys = None
        self.finished = False

    def verify(self, envelope, fields):
        envelope = object_fields(envelope, required={'payload', 'signature'}, optional=set(), path='signed packet')
        row = object_fields(envelope['payload'], required=set(self.context) | fields | {'node_id'},
                            optional=set(), path='payload')
        node = identifier(row['node_id'], 'node')
        if node not in self.identities or any(row[k] != v for k, v in self.context.items()):
            raise ValidationError('Unauthorized identity or stale round/model context')
        try:
            signature = bytes.fromhex(envelope['signature'])
            self.identities[node].verify(signature, canonical(row))
        except (InvalidSignature, ValueError, TypeError) as error:
            raise ValidationError('Invalid participant signature') from error
        return row

    def establish(self, announcements):
        if self.keys is not None or self.finished:
            raise ValidationError('Round already established/consumed')
        if not isinstance(announcements, list) or len(announcements) != len(self.identities):
            raise ValidationError('All authenticated peers must announce keys')
        keys = {}
        for envelope in announcements:
            row = self.verify(envelope, {'public_key'})
            if row['node_id'] in keys:
                raise ValidationError('Duplicate participant')
            try:
                keys[row['node_id']] = bytes.fromhex(row['public_key'])
            except (ValueError, TypeError) as error:
                raise ValidationError('Invalid ephemeral public key') from error
        transcript(keys, self.context['nonce'])
        self.keys = keys
        return dict(keys)

    def aggregate(self, envelopes):
        if self.finished or self.keys is None:
            raise ValidationError('Round unavailable or replayed')
        self.finished = True  # Any attempted completion consumes this round.
        if not isinstance(envelopes, list) or len(envelopes) != len(self.identities):
            LOGGER.warning('masked_round_aborted reason=incomplete_roster')
            raise ValidationError('Dropout: abort; never aggregate a partial roster')
        packets = []
        for envelope in envelopes:
            row = self.verify(envelope, {'masked', 'transcript'})
            packets.append({k: row[k] for k in ('node_id', 'masked', 'transcript')})
        result = aggregate(packets, self.keys, self.context['nonce'])
        LOGGER.info('masked_round_completed round=%d participants=%d', self.context['round'], len(packets))
        return result
