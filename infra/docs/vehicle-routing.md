# Vehicle routing with capacity and delivery windows

Implemented in `optimization/routing/` using the existing OR-Tools dependency.
No new install, network service, database, or vehicle dispatch is required.

## Run from infra/

```powershell
.\.venv\Scripts\python.exe -m optimization.routing --input optimization/routing/example.json --time-limit 3
.\.venv\Scripts\python.exe -m unittest optimization.tests.test_routing -v
```

On another machine, install the optional dependency from `infra/` using
`python -m pip install ".[transport]"` in a Python environment.

```python
from optimization.routing import recommend_routes

plan = recommend_routes(request, time_limit_seconds=3)
```

The synthetic example contains three PHCs, 15 standard boxes and two vans with
capacities 10 and 6. A feasible plan delivers all boxes and returns both used
vehicles to the warehouse within their shifts. Tied route choices can vary.

## Input contract

Use `optimization/routing/example.json` as the complete example.

- `request_id`, `travel_snapshot_id`, `quantity_unit`: backend references and a
  common vehicle-load unit. Convert medicine quantities into compatible loads
  before calling; a tablet and an oxygen cylinder are not interchangeable loads.
- `depot`: facility ID and opening/closing `window`.
- `stops`: unique facility IDs, positive delivery quantities, service durations,
  and service windows. Aggregate deliveries to one facility before calling.
- `vehicles`: unique IDs, positive capacity, and shift windows.
- `location_ids`: depot first, followed by stops in the exact declared order.
- `travel_time_minutes` and `distance_meters`: square directed matrices in that
  same order, using nonnegative integers and zero diagonals.

Times are minutes from one caller-defined planning origin, not clock strings.
All windows must fit within 0..10080 minutes. Service must start after opening
and finish by closing. Waiting is allowed. Departure and depot return must fit
the intersection of vehicle shift and depot hours. Each delivery is indivisible
and can be visited at most once; a quantity larger than every vehicle's capacity
will be left unserved rather than split.

There are limits of 200 stops, 50 vehicles, one million load units per stop or
vehicle, and a 60-second search budget. Matrices must describe finite traversable
connections; null/blocked arcs are not supported in this version. Use current
road travel estimates supplied by a trusted provider; distance alone does not
determine travel time. Do not use zero as a sentinel for a blocked road.

## Objective and output

The objective first favors delivered units, then reduces travel plus service
minutes. A bounded penalty makes one extra delivered unit dominate all possible
route time-cost savings. Waiting is reported but not charged in that objective.
There is no fairness, emergency weighting, or guarantee to maximize stop count.
The bounded search is heuristic; a feasible solution is not necessarily optimal.

Each used vehicle returns:

- Depot departure/return, route duration, delivered quantity and capacity.
- Ordered delivery stops with earliest arrival, scheduled service start and end.
- Directed legs with distance, travel time and waiting time.
- Total travel, waiting, service minutes, and distance.

Waiting is represented before service at the next location. A stop may be
reached before its window opens. Route duration equals travel + service + waiting.
Unused vehicles are omitted from `routes`.

`unserved_stops` means not included in this particular plan; it does not prove
that those stops are impossible to serve. Inspect `has_solution`, `solver_status`
and `optimality_proven`. If no incumbent is returned, status is `not_computed`,
unserved stops and numerical totals are null, and no plan should be executed.
An actual all-dropped plan is instead a feasible `unavailable` result.

The solver budget defaults to three seconds; validation and serialization add
overhead. CLI exit codes are 0 for a solution, 2 for invalid input, 3 for a solver
dependency/error, and 4 for no incumbent. JSON goes to stdout and logs to stderr.

## Connect to earlier transport recommendations

The transport allocator chooses sources and quantities; this router determines
whether a set of deliveries from one selected source fits a vehicle schedule.
The backend should group that source's approved candidate deliveries into stops,
provide compatible available vehicles and current matrices, then review any
unserved stops before approval/dispatch. A transport allocation alone does not
prove route feasibility. Multi-depot routing and joint allocation/routing remain
future work; do not independently assign the same vehicle to two source plans.

Fixed charges from the transport model apply per source-destination connection,
not per multi-stop vehicle trip. Routing output does not validate or recalculate
those charges. The backend must reconcile actual trip pricing separately.

The engine does not validate inventory, reserve stock or vehicles, enforce cold
chain, check driver qualifications/breaks, authenticate users, or issue dispatch
commands. Member 2 retains approval, revalidation, reservations and audit duties.

## Verification

Nine focused tests cover capacity shortages, indivisible stops, service windows,
shift boundaries, waiting, closed tours, distance accounting, input errors,
no-incumbent handling and the CLI. A small tour is compared with exhaustive
permutations. The existing redistribution/transport modules were not changed.

Reference: official OR-Tools [time windows](https://developers.google.com/optimization/routing/vrptw)
and [optional visit penalties](https://developers.google.com/optimization/routing/penalties).
