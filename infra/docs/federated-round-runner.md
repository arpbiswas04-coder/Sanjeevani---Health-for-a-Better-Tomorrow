# Run regional clients across rounds

Clients now support a bounded polling loop. The default still submits once, while
`--rounds N` waits for N distinct server challenges and submits at most once per
challenge during that process. The runner checks the server again after training
and discards the trained update if the round state changed.

From `infra/`, start the server as before. Run each regional client in its own
terminal so at least two nodes participate in the same rounds:

```powershell
.\.venv-federated\Scripts\python.exe -m federated.local client --node district-a --rounds 3 --max-wait-seconds 600
```

Use district-b and district-c in the other terminals. The direct
`federated.clients.https` CLI also accepts `--rounds`, `--max-wait-seconds` and
`--poll-seconds` (default 15). Round count is limited to 1–100, polling interval
to 5–300 seconds and elapsed-time budget to 1–86400 seconds.

For Docker, after preparing credentials and building the updated image:

```powershell
$env:FEDERATION_CLIENT_ROUNDS = '3'
$env:FEDERATION_CLIENT_MAX_WAIT_SECONDS = '600'
docker compose -f compose.yaml --profile training up -d
docker compose -f compose.yaml logs -f federation-client-a federation-client-b federation-client-c
```

Use the monitoring/Grafana overlay files too if those services are already part
of the running stack. Recreate exited client containers intentionally for another
run; submitting again in the same round can be rejected. The server remains
running after clients exit. No background task or scheduler has been started by
this implementation.

## Outcomes and failure behavior

- `submitted` / exit 0: the requested number of contributions were acknowledged
  as pending. This does not confirm successful aggregation; check server metrics.
- `timeout` / exit 3: the loop exhausted its elapsed-time budget before obtaining
  the requested number of acknowledgements. Output includes accepted submissions.
- Errors / exit 2: network, certificate, rate-limit, validation or submission
  failure. There is no automatic retry of ambiguous POST outcomes.
- Ctrl+C exits 130. Previously accepted updates remain pending at the server.

The timeout is checked between blocking operations; a training call or HTTP
request can overrun it. Training is not forcibly cancelled. HTTP operations retain
their existing socket timeout. Polling defaults fit the default identity rate
limit; tune both together if changing server limits.

Acknowledgement tracking is memory-only. A client restart forgets earlier
submissions, while a server restart changes challenges. The runner counts accepted
contributions rather than guaranteed consecutive or successfully aggregated rounds.
No automatic resume, durable delivery ledger or backoff/retry scheduler is supplied.

CLI output now uses a runner summary with `accepted_submissions` and
`aggregation_confirmed: false`; scripts expecting the old single acknowledgement
object must adapt. Credentials and challenges are not included in the summary.

Three focused mocked checks passed for one submission per challenge, timeout,
discarding stale training and refusing ambiguous retries. No real training,
waiting loop, network service or full test suite ran.
