# Federation monitoring

The HTTPS coordinator exposes `GET /metrics` in Prometheus text format. It
requires a trusted client certificate whose sole Sanjeevani URI identity is
`urn:sanjeevani:monitor`. Participant certificates cannot read metrics; monitoring
certificates cannot fetch training rounds or submit updates. The local provisioner
now creates a `monitor/` certificate bundle without any HMAC keys.

Metrics include accepted/rejected HTTP update counts, closed/insufficient rounds,
model version, next round, counts of nodes by last recorded status, last round
close time, aggregation duration and last successful checkpoint time. No model
parameters, losses, training sample counts, patient data or credentials are exposed.

Counters and timing gauges reset on process restart. Model/round/node state can
come from a restored checkpoint. Node status describes the last recorded round,
not current connectivity. Duration measures synchronous aggregation only, not
the training/waiting window. Rejection counts exclude TLS-handshake failures.

## Start with Compose

From `infra/`, provision an unexpired `local-dev` bundle using the current helper
if none exists. Older bundles without `monitor/` are not automatically upgraded:
provision a new named bundle and override all server/client/monitor mounts together.
Do not overwrite keys or combine certificates from different bundle CAs.

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local provision
docker compose -f compose.yaml -f compose.monitoring.yaml config --quiet
docker compose -f compose.yaml -f compose.monitoring.yaml up --build -d
```

Skip provisioning if a suitable bundle already exists. The overlay starts
Prometheus without starting the training-profile clients. Visit
`http://127.0.0.1:9090` and inspect the `federation` target and Alerts page.
Training commands remain in the [Docker guide](federated-docker.md).

Prometheus scrapes over mutually authenticated HTTPS every 15 seconds. It shares
the server's network namespace to use the localhost certificate and mounts only
the monitoring credentials. Its UI is published on host loopback, without login;
other containers sharing/reaching that namespace can also access it. This is a
private development configuration, not fully authenticated dashboard hosting.

Storage is bounded temporary memory: up to 24 hours/128 MB retention in a 256 MB
tmpfs. Metrics disappear when the container stops; model checkpoints remain in
their separate persistent volume. Match `MEMBER4_UID` to the credential owner on
Linux, as described in the Docker guide.

## Alerts and interpretation

| Alert | Meaning |
| --- | --- |
| FederationScrapeUnavailable | Scraping failed for a minute; inspect server and certificate expiry |
| FederationRoundStalled | No round closed for five minutes, sustained another minute |
| FederationInsufficientParticipants | At least two insufficient rounds observed in ten minutes |

The stalled threshold assumes the default 120-second rounds. Adjust it when
changing the server interval. Insufficient-participant alerts are expected when
the server runs without manual clients. Alerts appear in Prometheus only: no
Alertmanager, email or external notifications are configured. An optional
[Grafana dashboard overlay](federated-grafana.md) is now available separately.

Useful queries: `sanjeevani_federation_model_version`,
`sanjeevani_federation_nodes_missing`, and
`rate(sanjeevani_federation_updates_rejected_total[5m])`.

Stop using both files, retaining checkpoint data:

```powershell
docker compose -f compose.yaml -f compose.monitoring.yaml down
```

Local runtime update: authenticated scraping succeeded, and promtool validated
the mounted config and all three rules. External alert delivery remains unconfigured.
To validate again after configuration changes (credentials must exist):

```powershell
docker compose -f compose.yaml -f compose.monitoring.yaml run --rm --no-deps --entrypoint /bin/promtool prometheus check config /etc/prometheus/federation.yml
```

Configuration references: [Prometheus TLS scrape settings](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
and [text exposition format](https://prometheus.io/docs/instrumenting/exposition_formats/).
