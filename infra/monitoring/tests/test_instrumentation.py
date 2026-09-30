import asyncio
from pathlib import Path
import tempfile
import unittest
from monitoring.runtime.instrumentation import MetricsApp
from optimization.common import telemetry


class MetricsTests(unittest.TestCase):
    def test_auth_redaction_and_failure_count(self):
        async def backend(scope, receive, send):
            await send({'type':'http.response.start','status':503,'headers':[]})
            await send({'type':'http.response.body','body':b'failed'})
        with tempfile.TemporaryDirectory() as folder:
            key=Path(folder)/'token'; key.write_text('x'*40)
            wrapper=MetricsApp(backend,key,lambda:'sanjeevani_dependency_up{service="postgres"} 0\n')
            async def request(path,headers=[]):
                messages=[]
                async def send(value): messages.append(value)
                await wrapper({'type':'http','method':'GET','path':path,'headers':headers},None,send)
                return messages
            self.assertEqual(asyncio.run(request('/internal/metrics'))[0]['status'],403)
            asyncio.run(request('/api/private-patient-id'))
            response=asyncio.run(request('/internal/metrics',[(b'authorization',b'Bearer '+b'x'*40)]))
            self.assertEqual(response[0]['status'],200)
            content=response[1]['body'].decode()
            self.assertIn('status="5xx"',content)
            self.assertNotIn('private-patient-id',content)
            self.assertNotIn('x'*40,content)
            self.assertIn('service="postgres"} 0',content)

    def test_optimizer_exception_measured_without_changing_error(self):
        @telemetry.measured('optimizer','redistribution')
        def fail(): raise ValueError('expected')
        with self.assertRaisesRegex(ValueError,'expected'): fail()
        self.assertIn('kind="optimizer",name="redistribution",status="error"',telemetry.render())
