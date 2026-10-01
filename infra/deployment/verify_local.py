"""Read-only acceptance checks against the local synthetic Docker demo."""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import ssl
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch(url, *, context=None, headers=None, structured=True):
    with urlopen(Request(url, headers=headers or {}), timeout=8, context=context) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Response too large")
        return json.loads(raw) if structured else raw.decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monitoring", action="store_true")
    parser.add_argument("--grafana", action="store_true")
    parser.add_argument("--observability", action="store_true")
    args = parser.parse_args()
    checks = {}

    def check(name, operation):
        try:
            checks[name] = {"passed": bool(operation())}
        except (OSError, ValueError, KeyError, TypeError, HTTPError, URLError):
            checks[name] = {"passed": False, "reason": "unavailable_or_invalid_response"}

    check("backend_health", lambda: fetch("http://127.0.0.1:8000/api/v1/health").get("status") == "ok")
    check("frontend_spa", lambda: 'id="root"' in fetch("http://127.0.0.1:8080/member4-demo", structured=False))
    monitor = ROOT / "federated/secrets/local-dev/monitor"

    def metrics():
        context = ssl.create_default_context(cafile=str(monitor / "ca.pem"))
        context.load_cert_chain(str(monitor / "cert.pem"), str(monitor / "key.pem"))
        return "sanjeevani_federation_" in fetch("https://127.0.0.1:8443/metrics", context=context, structured=False)

    check("federation_authenticated_metrics", metrics)

    def unauthenticated_rejected():
        context = ssl.create_default_context(cafile=str(monitor / "ca.pem"))
        try:
            fetch("https://127.0.0.1:8443/metrics", context=context, structured=False)
        except HTTPError as error:
            return error.code in (401, 403)
        except (ssl.SSLError, URLError) as error:
            reason = getattr(error, "reason", error)
            # Connection refusal is not evidence of authentication enforcement.
            return isinstance(error, ssl.SSLError) or isinstance(reason, ssl.SSLError)
        return False

    check("federation_missing_certificate_rejected", unauthenticated_rejected)
    if args.observability:
        def backend_metrics():
            token = (monitor.parent / "metrics-token").read_text().strip()
            value = fetch("http://127.0.0.1:8000/internal/metrics",
                          headers={"Authorization": "Bearer " + token}, structured=False)
            return all(metric in value for metric in (
                'sanjeevani_dependency_up{service="postgres"} 1',
                'sanjeevani_dependency_up{service="redis"} 1',
                'sanjeevani_operation_calls_total{kind="http",name="health",status="2xx"}'))
        def metrics_denied():
            try:
                fetch("http://127.0.0.1:8000/internal/metrics", structured=False)
            except HTTPError as error:
                return error.code == 403
            return False
        def backend_scrape():
            value = fetch("http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22backend%22%7D")
            results = value["data"]["result"]
            return len(results) == 1 and results[0]["value"][1] == "1"
        check("backend_authenticated_metrics_and_dependencies", backend_metrics)
        check("backend_metrics_missing_token_rejected", metrics_denied)
        check("prometheus_backend_scrape", backend_scrape)
    if args.monitoring or args.grafana or args.observability:
        def scrape():
            value = fetch("http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22federation%22%7D")
            results = value["data"]["result"]
            return value["status"] == "success" and len(results) == 1 and results[0]["value"][1] == "1"
        check("prometheus_federation_scrape", scrape)
    if args.grafana:
        def dashboard():
            password = (monitor.parent / "grafana-admin-password").read_text().strip()
            token = base64.b64encode(("admin:" + password).encode()).decode()
            value = fetch("http://127.0.0.1:3000/api/dashboards/uid/sanjeevani-federation",
                          headers={"Authorization": "Basic " + token})
            return value["dashboard"]["uid"] == "sanjeevani-federation" and len(value["dashboard"]["panels"]) == 8
        check("grafana_provisioned_dashboard", dashboard)
        if args.observability:
            def application_dashboard():
                password = (monitor.parent / "grafana-admin-password").read_text().strip()
                token = base64.b64encode(("admin:" + password).encode()).decode()
                value = fetch("http://127.0.0.1:3000/api/dashboards/uid/sanjeevani-application",
                              headers={"Authorization": "Basic " + token})
                return value["dashboard"]["uid"] == "sanjeevani-application" and len(value["dashboard"]["panels"]) == 9
            check("grafana_application_dashboard", application_dashboard)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks,
              "passed": all(value["passed"] for value in checks.values()),
              "scope": "Local scaffold, authenticated metrics and optional monitoring; business APIs and clinical correctness not assessed"}
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="acceptance-", dir=output,
                                     encoding="utf-8", delete=False) as stream:
        json.dump(report, stream, indent=2)
        filename = stream.name
    print(json.dumps({**report, "evidence_file": filename}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
