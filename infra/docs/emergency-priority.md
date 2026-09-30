# Configurable emergency priority scoring

Implemented under `optimization/emergency/` with no external dependencies.
Scores describe facility-level operational pressure. They are not patient-level
triage, clinical thresholds, or an instruction to move medical resources.

## Run from infra/

```powershell
.\.venv\Scripts\python.exe -m optimization.emergency --demo
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_emergency -v
```

The synthetic demo refreshes built-in example timestamps. PHC A scores **0.555**;
the facility with missing data remains unscored. To evaluate supplied data, use
`--input request.json --policy policy.json`; those timestamps are not rewritten.

```python
from optimization.emergency import score_emergency_priorities

result = score_emergency_priorities(request, policy)
```

If policy is omitted, the packaged `policy.example.json` supplies the assignment's
example weights. Weights are configuration data, not repeated constants in code.

| Factor | Example weight |
| --- | ---: |
| Disease growth | 0.30 |
| Resource shortage | 0.25 |
| Bed pressure | 0.15 |
| Workforce shortage | 0.10 |
| Vulnerable population | 0.10 |
| Transport disruption | 0.10 |

## Contract with Member 3

The inspected Member 3 risk-scoring modules are still placeholders. This is a
provisional contract; integration with actual models remains pending.

Each request contains `request_id`, `snapshot_id`, timezone-aware `captured_at`,
`normalization_version` and `facilities`. Each facility has a unique
`facility_id` and `signals` object, keyed by the six factor names in the example.
Each supplied signal has `value`, `observed_at`, and `source_version`.

Values must already be normalized to **0..1**, with higher values meaning more
pressure. The engine rejects raw percentages, counts, non-finite numbers, numeric
strings, and booleans. It does not invent min/max ranges or rescale the facilities
in the current request. Member 3 and the backend must define factor meanings,
consistent forecast horizons, geographic scope and the normalization method.
The request normalization version must match the selected policy exactly.

Policy requires `policy_version`, `normalization_version`, `max_age_seconds`,
and all six weights. Weights must be nonnegative and sum to exactly 1. A zero
weight explicitly disables that factor. Change the policy version whenever
weights, normalization assumptions or freshness requirements change.

## Computation and missing information

For each complete facility:

```text
score = sum(normalized factor value × configured weight)
```

Decimal arithmetic is used for the weighted calculation and ranking. JSON
numbers may have normal floating-point display precision. The engine records
each factor's value, weight, contribution, observation time and source version.
Facilities are ranked by descending score; equal scores receive the same rank
and use facility ID for stable display order (e.g. ranks 1, 1, 3).

Any missing/null, stale or post-snapshot observation for a positive-weight factor
leaves that facility **unscored**, with null score and rank. No zero imputation or
renormalization occurs. A genuine numeric zero remains valid. Disabled factors
do not block scoring, although malformed supplied values still fail validation.
`weight_coverage` measures available valid input weight; it is not confidence.

The example freshness limit is one hour, a prototype configuration. Both the
snapshot and required signals must be younger than that limit. A stale or
future-dated whole snapshot rejects the request. Each scored facility's
`valid_until` is constrained by its oldest required observation and snapshot.
`now=` exists for deterministic tests; use the server clock in production.

## Response and integration

`ranked_facilities` contains scored facilities. `unscored_facilities` preserves
missing-data cases and their reasons; never hide these or display them as lowest
priority. Results also include policy/input versions, generation time, counts,
and recommendation/approval flags. No low/medium/high clinical categories or
unsupported confidence scores are assigned.

Member 1 can display the ordered facilities, factor contributions and separate
data-quality issues. Member 2 should authenticate requests, obtain trusted
inputs, persist/audit the result and recheck validity before using it in a
resource recommendation. The [resource recommendation wrapper](emergency-resource-recommendations.md)
now connects scores to transport constraints through a three-stage objective.
Do not override eligibility or approval constraints using a high score.

CLI exit 0 means evaluation completed, even when every facility is unscored;
exit 2 means invalid/unreadable input. JSON goes to stdout and summary logs to
stderr. No service is started, model is trained or resource is allocated.

Ten focused tests cover the example formula, configurable weights, normalization
validation, ties, missing/stale inputs, expiry, zero values, disabled factors,
malformed data, default packaged configuration and the synthetic CLI demo.
