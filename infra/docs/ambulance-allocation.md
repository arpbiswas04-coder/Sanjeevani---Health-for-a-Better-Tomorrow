# Ambulance eligibility and allocation

Implemented in `optimization/ambulance/`, using only the Python standard library.
This is a single-request operational recommendation, not clinical triage or an
automatic dispatch system. The inspected Member 2 backend has no ambulance model
or endpoint yet, so this JSON contract awaits backend integration.

## Run from infra/

```powershell
.\.venv\Scripts\python.exe -m optimization.ambulance --demo
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_ambulance -v
```

The synthetic demo refreshes only its built-in example's timestamps and chooses
`amb-a` (ETA 8 minutes), with `amb-b` as an alternative. The faster `amb-c` is
excluded because it is busy, reserved, and missing the required demo equipment.
`--input request.json` evaluates real supplied timestamps without rewriting them;
`--policy policy.json` optionally overrides configuration. Do not treat the
example's fictitious equipment/capability labels as medical requirements.

```python
from optimization.ambulance import recommend_ambulance

result = recommend_ambulance(request, {
    "max_age_seconds": 120,
    "max_eta_minutes": None,
    "max_alternatives": 3,
})
```

## Inputs and filtering

The full schema is illustrated by `optimization/ambulance/example.json`.
Required request fields: request ID, snapshot ID, timezone-aware capture time,
emergency type, required equipment identifiers, patient count, and candidates.
The backend supplies requirements from authorized operational policy; this code
does not infer them from symptoms, age, diagnosis, or text descriptions.

Each candidate explicitly supplies:

- Ambulance ID and status: available, busy, offline, or maintenance.
- Boolean reservation, crew-ready and serviceable flags.
- Patient capacity, equipment identifiers and supported emergency types.
- ETA in minutes and distance in kilometres; either may be null.
- `observed_at` for availability/equipment/crew information, and `eta_observed_at`
  for the ETA and associated location/distance observation.

Eligibility requires an available, unreserved, serviceable vehicle, a ready
crew, sufficient capacity, all required equipment, supported emergency type,
fresh observations and a known ETA. An optional maximum ETA is a hard filter.
Unknown distance is allowed when ETA is known and is sorted after known
distances only when ETAs tie. Equipment/type identifiers are case-sensitive.
The backend must verify the crew flag includes qualifications appropriate to
the request; the flag is not an independent credential check.

The default freshness window is 120 seconds, a configurable prototype setting,
not a clinically validated operating standard. Snapshot age must be strictly
less than the limit. Stale snapshots fail validation; stale candidates are
excluded individually. Observations after snapshot capture are excluded as
inconsistent. Invalid types, malformed timestamps, and duplicate IDs fail the
whole request, rather than silently accepting potentially corrupt data.

## Ranking and response

Eligible candidates are sorted by ETA, then distance, then ambulance ID. There
is no opaque confidence score or invented clinical weighting. Response fields:

- `recommended`: top candidate, or null when none qualifies.
- `alternatives`: next candidates, up to the configured count (default 3).
- `rejected_candidates`: specific rejection reasons and missing equipment.
- Eligible count, omitted alternatives count, input references and policy.
- Per-candidate `valid_until` and an overall expiry bounded by the oldest
  timestamp among the returned recommendation/alternatives and the snapshot.
- `recommendation_only: true` and `approval_required: true`.

`no_eligible_ambulance` is a valid result, not permission to relax constraints.
The backend should route that outcome to its authorized dispatcher/escalation
workflow. Exit 0 means a valid evaluation, including no eligible ambulance;
exit 2 means invalid/unreadable input. JSON uses stdout; logs use stderr without
patient details. `now=` supports deterministic tests, not caller-controlled
production freshness bypasses.

## Backend handoff

Add a permission-protected endpoint that obtains trusted fleet/ETA snapshots,
calls this module, and persists the result with an audit trail. Before dispatch,
an authorized user must approve and the backend must atomically recheck and
reserve the chosen vehicle. Recompute when expired. This function neither
reserves nor dispatches vehicles and cannot coordinate concurrent requests;
separate calls may recommend the same ambulance. An alternative is subject to
the same checks as the top candidate.

No new dependency, map API, live service, or backend clone change was introduced.
Nine focused tests cover eligibility, capacity, expiry boundaries, unknown ETAs,
deterministic ties, configuration, invalid data and the synthetic demo CLI.
