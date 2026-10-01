# Emergency scores connected to constrained allocation

From `infra/`, run the synthetic demo:

```powershell
.\.venv\Scripts\python.exe -m optimization.emergency --resources --demo
```

`optimization.emergency.resources.recommend_emergency_resources(request,
score_policy)` accepts `transport_request`, `risk_request`, and timezone-aware
`inventory_captured_at`. The nested requests use the existing contracts and must
share a request ID. Each transport destination must have a complete fresh score;
unrelated scored facilities are rejected. See `resource-example.json` in the
emergency module. Inventory freshness defaults to 300 seconds.

The objective order is: maximize fulfilled units, preserve that total and
maximize priority-weighted fulfillment, then preserve both and minimize cost.
Scores are multiplied by 1,000,000 and rounded half-up for integer coefficients.
Zero scores remain eligible; missing scores never become zero. Stock, batch,
expiry and lane caps remain hard constraints. This is a prototype operational
policy, not clinical triage or a fairness guarantee.

The example recommends 8 units to the higher-scored facility and 2 to the other,
with 6 unresolved units and synthetic cost of 102 paise.

The response contains full `scoring`, nested `allocation`, policy/input versions,
approval flags and earliest score/inventory `valid_until`. Status values:

- `recommended`: a feasible allocation exists; inspect objective proof flags.
- `needs_data_review`: missing/stale scores block the plan without invoking the solver.
- `no_solution`: no incumbent; shortage totals remain unknown.
- `expired_during_computation`: retained output is for inspection; recompute it.

Each solver phase runs only after proving the prior objective. A timeout retains
the last incumbent and reports `fulfillment_optimal`, `priority_optimal`, and
`cost_optimal` accurately. Ordinary transport calls without priority weights
retain their two-stage behavior. `now=` is a test hook, not a production override.

CLI: `--resources --input request.json` and optional `--policy policy.json`.
Exit codes: 0 recommended, 2 invalid input, 3 solver error, 4 data review/expired/no
incumbent. The scoring-only CLI is unchanged. Member 2 must authenticate, persist,
approve and atomically recheck/reserve stock. Routing feasibility is separate.

Verification: 31 scoring/transport/integration tests passed, including 30 new
small priority allocations compared with exhaustive enumeration.
