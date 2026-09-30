"""Local demonstration sink: stores bounded counts only, never alert payloads."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

COUNTS = {'firing': 0, 'resolved': 0, 'demo_firing': 0, 'demo_resolved': 0}


class Receiver(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(3)

    def log_message(self, *args):
        pass

    def respond(self, code, value):
        raw = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/health':
            return self.respond(200, {'status': 'ok', 'scope': 'local-only'})
        if self.path == '/counts':
            return self.respond(200, COUNTS)
        self.respond(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path != '/alerts':
            return self.respond(404, {'error': 'not_found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536 or self.headers.get('Transfer-Encoding'):
                raise ValueError('length')
            payload = json.loads(self.rfile.read(length))
            alerts = payload['alerts']
            if not isinstance(alerts, list) or len(alerts) > 100:
                raise ValueError('alerts')
            increments = {key: 0 for key in COUNTS}
            for alert in alerts:
                status = alert['status']
                if status not in ('firing', 'resolved'):
                    raise ValueError('status')
                increments[status] += 1
                if alert.get('labels', {}).get('alertname') == 'Member4LocalDemo':
                    increments['demo_' + status] += 1
            for key, count in increments.items():
                COUNTS[key] += count
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            return self.respond(400, {'error': 'invalid_alert'})
        self.respond(200, {'accepted': True})


if __name__ == '__main__':
    HTTPServer(('0.0.0.0', 9094), Receiver).serve_forever()
