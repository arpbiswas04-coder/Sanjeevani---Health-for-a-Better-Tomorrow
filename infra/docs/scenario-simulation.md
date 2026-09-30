# Redistribution what-if simulation

The first simulation module compares a baseline inventory snapshot with independent
disruption scenarios. It reuses the validated single-destination redistribution
engine. It never changes live stock, submits transfers or calls a backend.

From `infra/`:

```powershell
.\.venv\Scripts\python.exe -m optimization.simulation --demo
.\.venv\Scripts\python.exe -m optimization.simulation --input optimization/simulation/example.json
```

The example compares normal conditions with a demand increase, a source outage,
and expiry after 60 days. No external dependencies or forecast models are needed.

## Input

Provide `baseline` using the existing [redistribution contract](redistribution-contract.md),
optional `policy`, and 1–50 `scenarios`. Each scenario requires a unique
`scenario_id` and may include:

| Field | Meaning |
| --- | --- |
| `required_quantity` | Absolute replacement demand for this scenario |
| `elapsed_days` | Subtract 0–3650 days from every source batch's remaining expiry |
| `source_changes` | One change per known source facility |
| `source_changes[].unavailable` | Set usable surplus to zero for an outage or blocked access |
| `source_changes[].lost_safe_surplus` | Reduce baseline surplus by a nonnegative integer, at most the original surplus |
| `source_changes[].transport_cost_per_unit_paise` | Replace the source's linear unit cost with a nonnegative integer |

Each source change requires `facility_id`. Unknown or repeated sources and
unsupported fields are rejected. Unavailability takes precedence over surplus loss.
Every scenario starts from the original baseline, not the previous scenario.
At most 1000 baseline sources and a 1 MiB CLI input file are accepted.

## Output

Results include the baseline recommendation, scenario assumptions, each transformed
snapshot and recommendation, and signed differences for required/fulfilled quantity,
unresolved shortage and estimated cost. A positive shortage delta means additional
unmet demand. Lower cost alone is not an improvement: an outage can reduce cost
because fewer units are delivered.

The output carries `simulation_only: true`, an algorithm version and a canonical
input SHA-256 for replay tracking. Volatile recommendation UUIDs/timestamps are
removed so identical input produces identical output under the same implementation.
The input itself is never mutated. Do not submit these simulated outputs directly
to an approval workflow: generate a new recommendation from a fresh live snapshot.

## Current scope

For successive periods with stock carried forward, use the separate
[timeline mode](inventory-timeline.md). Independent scenarios here retain their
original baseline-reset behavior.

This is a static what-if foundation, not the complete digital twin. It supports one
medicine, one destination and one selected batch per source with linear transport
cost. Elapsed time changes shelf life only; it does not predict consumption,
deliveries, demand or disease spread. Road/vehicle constraints, multi-step inventory
evolution, Member 3 forecast integration and resilience scoring remain pending.

Two focused checks passed for scenario isolation, exact repeatability, expected
shortages and invalid source changes. No broad suite or model training ran.

```powershell
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_simulation -v
```
