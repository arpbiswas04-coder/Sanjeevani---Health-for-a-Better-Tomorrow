# Staff redistribution recommendations

Implemented in `optimization/workforce/` using the existing OR-Tools dependency.
The inspected Member 2 backend has no staffing models yet; this normalized
contract awaits live integration. Nothing changes a roster or dispatches staff.

## Run from infra/

```powershell
.\.venv\Scripts\python.exe -m optimization.workforce --demo
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_workforce -v
```

The synthetic example sends the specialist-qualified worker to the specialist
request and the other worker to the general request, retaining one source worker.
Labels are fictitious; no real credential or clinical requirement is inferred.

```python
from optimization.workforce import recommend_staff

result = recommend_staff(request, max_age_seconds=300, time_limit_seconds=5)
```

## Input

See `optimization/workforce/example.json`. All timestamps must have timezones.

- `request_id`, `snapshot_id`, `captured_at`, one common `shift_start`/`shift_end`.
- `staffing`: facility/role, projected on-duty count, and minimum required count.
- `workers`: unique IDs, source facility, exact role, verified skill identifiers,
  availability/reservation/transferability/rest readiness flags, full availability
  interval and latest observation time.
- `demands`: destination/role, required count, and required skills.
- `lanes`: source/destination, outbound and return travel minutes.

All candidates must be included in the declared source on-duty count. Other
nontransferable staff can be counted without appearing as candidates. The backend
must ensure these counts describe the whole requested absence, including travel,
and account for existing commitments. Incoming staff never increase export limits
within this solve. Source minimums are mandatory configuration, not inferred.

## Hard constraints and objective

Each worker can receive at most one assignment. Roles match exactly and every
required skill must be present. Unavailable/reserved/nontransferable/unrested or
stale candidates are excluded. Worker availability must cover travel to the
destination, the complete shared shift and return travel. Departure cannot be
in the past. Missing lanes, self-transfers, and cross-role substitutions are
not allowed. Export count per source/role is capped at
`max(0, on_duty - minimum_required)`. An already deficient source exports zero;
its pre-existing deficit is reported through its staffing balance, not repaired.

Maximize filled positions first, then minimize total round-trip travel minutes.
A bounded integer objective coefficient makes one additional filled position
dominate all possible travel-cost savings. No emergency weighting, fairness,
multi-shift schedule, skill substitution or labor-law rules are inferred.
Readiness flags and skill labels require trusted operational verification.

## Output and limitations

Results include assignments, departures/returns, unmet demand by destination/role,
remaining source staffing, exclusions, solver status and optimality flag. An
unassigned eligible worker may be omitted because another assignment was better;
exclusion lists only describe eligibility failures, not every unselected worker.

`recommended` means a feasible incumbent exists, even when it fills zero positions.
Inspect shortages. `no_solution` leaves totals unknown. `expired_during_computation`
retains the plan for review only. Validity is bounded by snapshot/selected-worker
freshness and the earliest departure. Approval must occur before that deadline.
`now=` is a deterministic testing hook; production uses the server clock.

The default freshness limit is 300 seconds. Search budget is 5 seconds, maximum
60; validation/building add overhead. No solution is claimed optimal unless the
solver proves it. CLI `--input` does not refresh timestamps; `--demo` refreshes
only built-in synthetic data. Exit codes: 0 feasible recommendation, 2 invalid
input, 3 solver error, 4 no incumbent or expired result.

Member 2 must authenticate, validate qualifications and actual shift/rest policy,
approve, and atomically reserve workers and recheck source staffing. Concurrent
calls can otherwise recommend the same worker. This is a prototype recommendation
component and does not itself implement permission or employment-policy checks.

Focused tests cover skill matching, staffing floors, travel/shift coverage,
eligibility, freshness, inconsistent rosters, timeout/expiry and the CLI, with
25 small assignments independently enumerated for objective verification.
