"""Safe, bounded artifact intake for the supported synthetic federation model.

Expected version, preprocessing and digest must come from the trusted operator,
not from the artifact being checked. No pickle, imports or executable model code.
"""
import hashlib
import hmac
import json
from pathlib import Path
import re

from federated.strategies.fedavg import MODEL_SCHEMA, parameters
from optimization.common.validation import ValidationError, identifier, object_fields

MAX_BYTES = 65536


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError('Duplicate artifact field')
        result[key] = value
    return result


def load_artifact(path, *, expected_sha256, expected_version, expected_preprocessing):
    """Return validated parameters/provenance, without installing or loading code."""
    if not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValidationError('Expected SHA256 must come from a trusted release manifest')
    identifier(expected_version, 'expected_version')
    identifier(expected_preprocessing, 'expected_preprocessing')
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError('Artifact exceeds 64 KiB reference model limit')
    if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), expected_sha256):
        raise ValidationError('Artifact checksum mismatch')
    try:
        data = json.loads(raw, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValidationError('Artifact is not valid unambiguous JSON') from error
    data = object_fields(data, required={'artifact_schema', 'model_schema', 'model_version',
        'preprocessing_version', 'parameters'}, optional=set(), path='artifact')
    if data['artifact_schema'] != 'sanjeevani-model-artifact-v1' or data['model_schema'] != MODEL_SCHEMA:
        raise ValidationError('Unsupported artifact/model schema')
    if data['model_version'] != expected_version or data['preprocessing_version'] != expected_preprocessing:
        raise ValidationError('Artifact release/preprocessing mismatch')
    return {'parameters': parameters(data['parameters']), 'model_schema': MODEL_SCHEMA,
            'artifact_model_version': expected_version,
            'preprocessing_version': expected_preprocessing, 'sha256': expected_sha256}
