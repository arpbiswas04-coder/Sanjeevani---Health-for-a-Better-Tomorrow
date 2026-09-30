import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from federated.artifacts import load_artifact, MAX_BYTES
from federated.server.coordinator import Coordinator
from optimization.common.validation import ValidationError


class ArtifactTests(unittest.TestCase):
    def test_validated_parameters_initialize_reference_coordinator(self):
        model = {'artifact_schema': 'sanjeevani-model-artifact-v1',
                 'model_schema': 'synthetic-linear-v1', 'model_version': 'demo-v1',
                 'preprocessing_version': 'identity-v1', 'parameters': {'weight': 2, 'bias': 1}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.json'
            raw = json.dumps(model).encode()
            path.write_bytes(raw)
            result = load_artifact(path, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                   expected_version='demo-v1', expected_preprocessing='identity-v1')
            coordinator = Coordinator({'a': 'region-a'}, min_clients=1, initial_model=result['parameters'])
            self.assertEqual(coordinator.state()['parameters'], {'weight': 2, 'bias': 1})
            for updates in ({'expected_sha256': '0' * 64}, {'expected_version': 'demo-v2'},
                            {'expected_preprocessing': 'changed'}):
                options = dict(expected_sha256=hashlib.sha256(raw).hexdigest(),
                               expected_version='demo-v1', expected_preprocessing='identity-v1')
                with self.assertRaises(ValidationError):
                    load_artifact(path, **(options | updates))

    def test_unsafe_or_incompatible_payloads_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model'
            for raw in (b'\x80\x04pickle', b'{"x":1,"x":2}', b'[]', b' ' * (MAX_BYTES + 1),
                        json.dumps({'artifact_schema': 'sanjeevani-model-artifact-v1',
                            'model_schema': 'synthetic-linear-v1', 'model_version': 'v1',
                            'preprocessing_version': 'p1',
                            'parameters': {'weight': float('nan'), 'bias': 1}}).encode()):
                path.write_bytes(raw)
                with self.assertRaises(ValidationError):
                    load_artifact(path, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                  expected_version='v1', expected_preprocessing='p1')
