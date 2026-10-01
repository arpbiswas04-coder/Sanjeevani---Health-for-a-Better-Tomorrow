"""Send a synthetic alert to loopback Alertmanager and verify firing/resolution."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import time
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]


def request(url, value=None):
    data = None if value is None else json.dumps(value).encode()
    with urlopen(Request(url, data=data, headers={'Content-Type': 'application/json'}), timeout=5) as response:
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError('Response exceeds limit')
        return json.loads(raw) if raw else None


def wait_count(key, baseline):
    end = time.monotonic() + 25
    while time.monotonic() < end:
        if request('http://127.0.0.1:9094/counts')[key] > baseline:
            return True
        time.sleep(1)
    return False


def main():
    before = request('http://127.0.0.1:9094/counts')
    now = datetime.now(timezone.utc)
    alert = {'labels': {'alertname': 'Member4LocalDemo', 'severity': 'warning', 'demo_run': uuid.uuid4().hex},
             'startsAt': now.isoformat(), 'endsAt': (now + timedelta(minutes=1)).isoformat()}
    request('http://127.0.0.1:9093/api/v2/alerts', [alert])
    firing = wait_count('demo_firing', before['demo_firing'])
    alert['endsAt'] = datetime.now(timezone.utc).isoformat()
    request('http://127.0.0.1:9093/api/v2/alerts', [alert])
    resolved = wait_count('demo_resolved', before['demo_resolved'])
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'firing_delivered': firing,
              'resolved_delivered': resolved, 'passed': firing and resolved,
              'scope': 'Local Alertmanager to local receiver only; no external delivery'}
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json',
                                     prefix='alerts-', dir=ROOT / 'outputs', delete=False) as stream:
        json.dump(report, stream, indent=2)
        report['evidence_file'] = stream.name
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
