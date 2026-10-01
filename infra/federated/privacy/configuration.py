"""Explicit configurable reference privacy. Disabled mode makes no privacy claim."""
import json
from pathlib import Path
from federated.privacy.gaussian import GaussianRelease, vector
from optimization.common.validation import ValidationError, object_fields


def policy(value):
    value = object_fields(value, required={'enabled', 'clipping_norm', 'noise_multiplier', 'delta', 'privacy_budget'},
                          optional=set(), path='privacy')
    if type(value['enabled']) is not bool:
        raise ValidationError('Privacy enabled must be boolean')
    legacy = {k: value[k] for k in ('clipping_norm', 'noise_multiplier', 'delta')}
    legacy['max_epsilon'] = value['privacy_budget']
    GaussianRelease(legacy)  # Validate even when disabled; no release is charged.
    return legacy


def load(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValidationError('Learning configuration exceeds limit')
    data = object_fields(json.loads(raw), required={'privacy', 'personalization'}, optional=set(), path='learning')
    policy(data['privacy'])
    from federated.clients.personalization import validate_config
    validate_config(data['personalization'])
    return data


class ConfiguredRelease:
    def __init__(self, config, *, ledger=None, node=None):
        validated = policy(config)
        self.enabled = config['enabled']
        if not self.enabled and ledger is not None:
            raise ValidationError('Do not attach a private ledger to a nonprivate control run')
        self.mechanism = GaussianRelease(validated, ledger=ledger, node=node)

    def release(self, values):
        return self.mechanism.release(values) if self.enabled else vector(values)
