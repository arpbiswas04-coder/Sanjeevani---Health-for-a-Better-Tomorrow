"""Bounded localhost-only TLS, readiness, CORS and access-control acceptance."""
from datetime import datetime, timezone
import json
from pathlib import Path
import ssl
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]


def run():
    bundle = ROOT/'federated/secrets/local-dev'
    context = ssl.create_default_context(cafile=str(bundle/'ingress/cert.pem'))
    def request(path, headers=None, method='GET', tls=context):
        try:
            with urlopen(Request('https://localhost:9443'+path, headers=headers or {}, method=method), context=tls, timeout=5) as response:
                return response.status, dict(response.headers), response.read(65536)
        except HTTPError as error:
            return error.code, dict(error.headers), error.read(65536)
    checks = {}
    status, headers, body = request('/api/v1/ready')
    checks['tls_identity_and_dependencies_ready'] = status == 200 and json.loads(body)['status'] == 'ok'
    checks['security_headers'] = headers.get('X-Content-Type-Options') == 'nosniff' and headers.get('X-Frame-Options') == 'DENY'
    checks['frontend_https'] = request('/')[0] == 200
    checks['internal_metrics_hidden'] = request('/internal/metrics')[0] == 404
    checks['metrics_without_client_identity_denied'] = request('/metrics/')[0] == 403
    context.load_cert_chain(str(bundle/'monitor/cert.pem'), str(bundle/'monitor/key.pem'))
    checks['metrics_without_bearer_denied'] = request('/metrics/')[0] == 403
    token = (bundle/'metrics-token').read_text().strip()
    checks['metrics_with_both_credentials'] = request('/metrics/', {'Authorization':'Bearer '+token})[0] == 200
    preflight = {'Origin':'https://untrusted.invalid', 'Access-Control-Request-Method':'GET'}
    checks['cors_unknown_origin_denied'] = 'access-control-allow-origin' not in {k.lower():v for k,v in request('/api/v1/health',preflight,'OPTIONS')[1].items()}
    preflight['Origin'] = 'https://localhost:9443'
    checks['cors_allowed_origin'] = {k.lower():v for k,v in request('/api/v1/health',preflight,'OPTIONS')[1].items()}.get('access-control-allow-origin') == preflight['Origin']
    checks['auth_route_rate_limited'] = 429 in [request('/api/v1/auth/member4-rate-probe')[0] for _ in range(8)]
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args): return None
    try:
        build_opener(NoRedirect).open('http://localhost:9080/api/v1/ready', timeout=5)
        checks['http_redirects_to_https'] = False
    except HTTPError as error:
        checks['http_redirects_to_https'] = error.code == 308 and error.headers.get('Location') == 'https://localhost:9443/api/v1/ready'
    return {'checked_at':datetime.now(timezone.utc).isoformat(), 'checks':checks, 'passed':all(checks.values()),
            'scope':'Local TLS and scaffold access controls; no business authorization acceptance'}


if __name__ == '__main__':
    report = run()
    output = ROOT/'outputs/ingress-acceptance.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)
