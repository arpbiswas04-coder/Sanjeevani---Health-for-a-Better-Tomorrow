from pathlib import Path
import sys
import unittest

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path:
    sys.path.insert(0, _infra)

from deployment.render_ingress import render


class IngressTests(unittest.TestCase):
    def test_origin_limits_and_protection(self):
        source = (Path(__file__).parents[2]/'nginx/member4-tls.conf').read_text()
        configured = render(source, 'https://demo.example:443', auth='3r/m')
        self.assertIn('return 308 https://demo.example:443$request_uri;', configured)
        self.assertIn('zone=auth:1m rate=3r/m;', configured)
        self.assertIn('ssl_verify_client optional;', configured)
        self.assertIn('if ($monitor_allowed = 0) { return 403; }', configured)
        self.assertIn('TLSv1.2 TLSv1.3', configured)

    def test_injection_plaintext_and_invalid_limits_fail(self):
        for origin in ('http://example.com', 'https://a;bad', 'https://u:p@example.com', 'https://example.com/path'):
            with self.assertRaises(ValueError): render('', origin)
        with self.assertRaises(ValueError): render('', 'https://example.com', auth='1r/s;evil')
