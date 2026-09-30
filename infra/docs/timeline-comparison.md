# Compare supply timelines

Timeline comparison runs a baseline schedule and up to ten alternatives against
the same initial snapshot and policy. Each alternative evolves independently and
must use the same ordered day offsets, preventing accidental comparisons of
different reporting windows. The underlying [timeline assumptions](inventory-timeline.md)
still apply; no live inventory or approvals are changed.

From `infra/`:

```powershell
.\.venv\Scripts\python.exe -m optimization.simulation --compare-timelines --demo
.\.venv\Scripts\python.exe -m optimization.simulation --compare-timelines --input optimization/simulation/comparison-example.json
```

Input contains `baseline` (initial redistribution snapshot), `baseline_periods`,
optional `policy`, and `scenarios`, each with a unique `scenario_id` and complete
`periods` array. Periods use the existing timeline contract including demand,
arrivals, losses and blocked sources. CLI modes `--timeline` and
`--compare-timelines` are mutually exclusive; the original independent what-if
mode remains the default.

Output contains full auditable traces plus summaries for delivered quantity,
unmet demand, arrivals, losses, expiry, transport cost, total demand, fulfillment
fraction, periods with shortages and ending surplus. Each scenario includes
scenario-minus-baseline deltas and per-day delivery/shortage differences.
Zero-demand fulfillment fractions and their undefined differences are `null`.
Fraction differences are fraction points, not relative percentage changes.

The demo delays a 500-unit supply arrival from day 1 to day 2 while preserving its
absolute expiry date. Unmet demand rises from 400 to 900 units; ending surplus rises
by 500 because late stock cannot satisfy a past period's demand. Unmet demand is
not backlogged in this model. Demand changes are permitted but then represent
additional changed assumptions; inspect demand deltas before interpreting effects.

Outputs are deterministic and include an input digest. No automatic best-scenario
ranking, clinical benefit claim or resilience score is assigned. Lower transport
cost alone can result from fewer deliveries. Forecast integration, destination
storage, travel delays and multiple simultaneous batches remain pending.

Two focused checks passed for expected delay effects, unchanged inputs, repeatable
results, zero-demand handling and incompatible day grids. No full suite or training
ran.
