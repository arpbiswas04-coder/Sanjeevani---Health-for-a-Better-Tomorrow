# Federation request rate limits

The HTTPS coordinator now applies a token bucket to each registered certificate
node identity and a separate bucket to the monitoring identity. Each bucket starts
with 10 tokens and refills at 30 requests per minute by default. GET and POST
requests for a participant share its bucket; a node cannot gain capacity by
switching endpoints or opening a new connection.

Limits apply after TLS and certificate identity checks, before update bodies are
read or admitted. Requests over budget receive HTTP 429 with a `Retry-After`
header in seconds and a closed connection. Invalid submissions and unknown paths
from valid participant identities also consume tokens. Rejected identities do not
create buckets, keeping memory bounded by the registered participant count.

Configure the direct HTTPS server using `--requests-per-minute` (1–6000) and
`--request-burst` (1–1000). Local and Docker launchers retain the defaults. The
monitor shares the configured rate/burst values but has its own budget; default
Prometheus scraping every 15 seconds is below the default limit.

`sanjeevani_federation_requests_rate_limited_total` counts throttled requests.
Throttled update POSTs also contribute to the existing rejected-update counter.
The client currently reports a failed request and does not automatically retry.
Fetch current round state before retraining/resubmitting after a wait.

Limits reset at server restart, use monotonic elapsed time, and are local to this
single-process development server. The limiter is not a distributed service and
requires synchronization if a concurrent HTTP runtime is introduced. It does not
limit TLS handshakes, invalid certificates, unsupported HTTP methods or slow
connections before authentication. Proxy-level connection/request controls and
production server hardening remain pending; this is not a denial-of-service guarantee.

Four focused limiter/metrics checks passed, including refill timing, independent
node budgets, bounded state, refusal before body/admission access, and existing
monitor authorization. No listeners, training or broad suite were run.
