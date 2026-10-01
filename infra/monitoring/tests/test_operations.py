import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path:
    sys.path.insert(0, _infra)

from deployment.operation_status import record
from monitoring.runtime.instrumentation import MetricsApp, operation_metrics


class OperationTests(unittest.TestCase):
    def test_status_retains_success_and_rejects_bad_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIn('operation="backup"} 0', operation_metrics(folder))
            record('backup', True, folder)
            first = json.loads((Path(folder)/'backup.json').read_text())
            record('backup', False, folder)
            second = json.loads((Path(folder)/'backup.json').read_text())
            self.assertEqual(first['last_success'], second['last_success'])
            self.assertIn('sanjeevani_scheduled_success{operation="backup"} 0', operation_metrics(folder))
            (Path(folder)/'restore.json').write_text('{"success":true,"last_attempt":-1}')
            self.assertIn('operation="restore"} 0', operation_metrics(folder))

    def test_readiness_is_distinct_from_liveness_and_sanitized(self):
        async def unused(*args):
            raise AssertionError('Readiness must be intercepted')
        async def request(path, probes):
            messages = []
            async def send(value): messages.append(value)
            await MetricsApp(unused, 'unused', lambda: probes)(
                {'type':'http','method':'GET','path':path}, None, send)
            return messages
        self.assertEqual(asyncio.run(request('/api/v1/live', ''))[0]['status'], 200)
        failed = asyncio.run(request('/api/v1/ready', 'postgres password or patient data'))
        self.assertEqual(failed[0]['status'], 503)
        self.assertEqual(failed[1]['body'], b'{"status":"unavailable"}')
        probes = '\n'.join(f'sanjeevani_dependency_up{{service="{name}"}} 1' for name in ('postgres','redis'))
        self.assertEqual(asyncio.run(request('/api/v1/ready', probes))[0]['status'], 200)
