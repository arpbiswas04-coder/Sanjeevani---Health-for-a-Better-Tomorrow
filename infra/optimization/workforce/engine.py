"""Single-shift, indivisible staff assignments using OR-Tools CP-SAT."""

import logging
from collections import Counter
from datetime import timedelta
from uuid import uuid4

from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

LOGGER = logging.getLogger(__name__)


def _rows(value, path, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise ValidationError(f"{path} must be an array with at most {limit} rows")
    return value


def _count(value, path, limit=10000):
    result = integer(value, path)
    if result > limit:
        raise ValidationError(f"{path} exceeds {limit}")
    return result


def _skills(value, path):
    labels = [identifier(v, path) for v in _rows(value, path, 100)]
    if len(set(labels)) != len(labels):
        raise ValidationError(f"{path} contains duplicates")
    return set(labels)


def _solve(cp, model, seconds):
    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    return solver, solver.solve(model)


from optimization.common.telemetry import measured


@measured("optimizer", "workforce")
def recommend_staff(request, *, max_age_seconds=300, time_limit_seconds=5, now=None):
    """Maximize filled staff positions, then minimize round-trip travel minutes.

    One shared shift, one assignment per worker, exact role matching. Source
    staffing floors are enforced per role without counting incoming staff.
    Qualification/readiness flags must come from the trusted backend.
    """
    current = utc_now(now)
    age_limit = integer(max_age_seconds, "max_age_seconds", 1)
    if age_limit > 86400: raise ValidationError("max_age_seconds exceeds 86400")
    seconds = nonnegative_number(time_limit_seconds, "time_limit_seconds")
    if not 0 < seconds <= 60: raise ValidationError("time_limit_seconds must be in (0, 60]")
    data = object_fields(request, required={"request_id", "snapshot_id", "captured_at", "shift_start", "shift_end",
                         "staffing", "workers", "demands", "lanes"}, optional=set(), path="request")
    ids = {key: identifier(data[key], key) for key in ("request_id", "snapshot_id")}
    captured = utc_timestamp(data["captured_at"], "captured_at")
    if not 0 <= (current - captured).total_seconds() < age_limit:
        raise ValidationError("Staffing snapshot is stale or future-dated")
    start, end = utc_timestamp(data["shift_start"], "shift_start"), utc_timestamp(data["shift_end"], "shift_end")
    if start < current or not 0 < (end - start).total_seconds() <= 7 * 86400:
        raise ValidationError("Shift must start no earlier than now and last at most seven days")
    staffing, workers, demands, lanes = {}, {}, {}, {}
    expiries = [captured + timedelta(seconds=age_limit), start]
    for raw in _rows(data["staffing"], "staffing", 1000):
        row = object_fields(raw, required={"facility_id", "role", "on_duty", "minimum_required"}, optional=set(), path="staffing row")
        key = (identifier(row["facility_id"], "staffing.facility_id"), identifier(row["role"], "staffing.role"))
        if key in staffing: raise ValidationError("Duplicate staffing facility/role")
        count = _count(row["on_duty"], "staffing.on_duty")
        minimum = _count(row["minimum_required"], "staffing.minimum_required")
        staffing[key] = {"on_duty": count, "minimum_required": minimum, "export_limit": max(0, count - minimum)}
    worker_counts = Counter()
    for raw in _rows(data["workers"], "workers", 500):
        row = object_fields(raw, required={"worker_id", "source_facility", "role", "skills", "available", "reserved",
                            "transferable", "rest_ready", "available_from", "available_until", "observed_at"},
                            optional=set(), path="worker")
        worker_id = identifier(row["worker_id"], "worker.worker_id")
        source = identifier(row["source_facility"], "worker.source_facility")
        role = identifier(row["role"], "worker.role")
        if worker_id in workers or (source, role) not in staffing:
            raise ValidationError("Worker is duplicated or lacks source staffing information")
        worker_counts[(source, role)] += 1
        skills = _skills(row["skills"], "worker.skills")
        for flag in ("available", "reserved", "transferable", "rest_ready"):
            if type(row[flag]) is not bool: raise ValidationError(f"worker.{flag} must be boolean")
        available_from = utc_timestamp(row["available_from"], "worker.available_from")
        available_until = utc_timestamp(row["available_until"], "worker.available_until")
        if available_from > available_until: raise ValidationError("Worker availability window is reversed")
        observed = utc_timestamp(row["observed_at"], "worker.observed_at")
        reasons = []
        if not row["available"]: reasons.append("not_available")
        if row["reserved"]: reasons.append("already_reserved")
        if not row["transferable"]: reasons.append("not_transferable")
        if not row["rest_ready"]: reasons.append("rest_not_confirmed")
        if observed > captured: reasons.append("observation_after_snapshot")
        elif (current - observed).total_seconds() >= age_limit: reasons.append("stale_worker_state")
        if staffing[(source, role)]["export_limit"] == 0: reasons.append("source_staffing_floor")
        workers[worker_id] = {"source": source, "role": role, "skills": skills, "from": available_from,
                              "until": available_until, "observed": observed, "reasons": reasons}
    if any(count > staffing[key]["on_duty"] for key, count in worker_counts.items()):
        raise ValidationError("Candidate roster exceeds declared on-duty source staffing")
    for raw in _rows(data["demands"], "demands", 100):
        row = object_fields(raw, required={"facility_id", "role", "required_staff", "required_skills"}, optional=set(), path="demand")
        key = (identifier(row["facility_id"], "demand.facility_id"), identifier(row["role"], "demand.role"))
        if key in demands: raise ValidationError("Duplicate demand facility/role")
        demands[key] = {"count": _count(row["required_staff"], "demand.required_staff"),
                        "skills": _skills(row["required_skills"], "demand.required_skills")}
    for raw in _rows(data["lanes"], "lanes", 2000):
        row = object_fields(raw, required={"source", "destination", "outbound_minutes", "return_minutes"}, optional=set(), path="lane")
        key = (identifier(row["source"], "lane.source"), identifier(row["destination"], "lane.destination"))
        if key in lanes or key[0] not in {s for s, _ in staffing} or key[1] not in {d for d, _ in demands}:
            raise ValidationError("Lane is duplicated or references unknown facilities")
        lanes[key] = (_count(row["outbound_minutes"], "lane.outbound_minutes", 10080),
                      _count(row["return_minutes"], "lane.return_minutes", 10080))
    edges, exclusions = {}, []
    for worker_id, worker in sorted(workers.items()):
        if worker["reasons"]:
            exclusions.append({"worker_id": worker_id, "destination": None, "reasons": worker["reasons"]})
            continue
        for (destination, role), demand in sorted(demands.items()):
            if role != worker["role"] or demand["count"] == 0: continue
            lane = lanes.get((worker["source"], destination))
            reasons = []
            if destination == worker["source"]: reasons.append("same_facility")
            if demand["skills"] - worker["skills"]: reasons.append("missing_required_skills")
            if lane is None: reasons.append("no_travel_lane")
            else:
                departure = start - timedelta(minutes=lane[0])
                returned = end + timedelta(minutes=lane[1])
                if departure < max(current, worker["from"]) or returned > worker["until"]:
                    reasons.append("travel_and_shift_outside_availability")
            if reasons:
                exclusions.append({"worker_id": worker_id, "destination": destination, "reasons": reasons})
            else:
                edges[(worker_id, destination)] = {"role": role, "cost": sum(lane), "departure": departure, "return": returned}
    if len(edges) > 5000: raise ValidationError("More than 5000 eligible worker/destination pairs")
    try:
        from ortools.sat.python import cp_model as cp
    except ImportError as exc:
        raise RuntimeError("Workforce allocation requires the infra[transport] extra") from exc
    model = cp.CpModel()
    variables = {key: model.new_bool_var(f"assignment_{i}") for i, key in enumerate(edges)}
    for worker_id in workers:
        model.add(sum(var for (w, _), var in variables.items() if w == worker_id) <= 1)
    for (destination, role), demand in demands.items():
        model.add(sum(var for (w, d), var in variables.items() if d == destination and workers[w]["role"] == role) <= demand["count"])
    for key, source in staffing.items():
        model.add(sum(var for (w, _), var in variables.items() if (workers[w]["source"], workers[w]["role"]) == key) <= source["export_limit"])
    # A single additional assignment dominates every possible travel-cost change.
    multiplier = 1 + sum(edge["cost"] for edge in edges.values())
    model.maximize(sum(var * (multiplier - edges[key]["cost"]) for key, var in variables.items()))
    if model.validate(): raise RuntimeError("Workforce model validation failed")
    solver, status = _solve(cp, model, seconds)
    has_solution = status in (cp.OPTIMAL, cp.FEASIBLE)
    assignments = []
    if has_solution:
        for (worker_id, destination), var in variables.items():
            if not solver.value(var): continue
            edge, worker = edges[(worker_id, destination)], workers[worker_id]
            expiries.extend([worker["observed"] + timedelta(seconds=age_limit), edge["departure"]])
            assignments.append({"worker_id": worker_id, "source": worker["source"], "destination": destination,
                                "role": worker["role"], "departure_at": edge["departure"].isoformat(),
                                "return_at": edge["return"].isoformat(), "travel_minutes": edge["cost"]})
    shortages = [{"facility_id": d, "role": role, "required_staff": demand["count"],
                  "unresolved_staff": demand["count"] - sum(a["destination"] == d and a["role"] == role for a in assignments)
                  if has_solution else None} for (d, role), demand in sorted(demands.items())]
    balances = [{"facility_id": s, "role": role, **row,
                 "remaining_staff": row["on_duty"] - sum(a["source"] == s and a["role"] == role for a in assignments)
                 if has_solution else None} for (s, role), row in sorted(staffing.items())]
    expiry = min(expiries)
    finished = utc_now() if now is None else current
    result = {**ids, "schema_version": "workforce-1.0", "recommendation_id": str(uuid4()),
              "generated_at": current.isoformat(), "valid_until": expiry.isoformat(),
              "recommendation_only": True, "approval_required": True, "has_solution": has_solution,
              "solver_status": solver.status_name(status), "optimality_proven": status == cp.OPTIMAL,
              "status": "expired_during_computation" if finished >= expiry else ("recommended" if has_solution else "no_solution"),
              "shift_start": start.isoformat(), "shift_end": end.isoformat(),
              "assignments": assignments, "shortages": shortages, "source_staffing": balances,
              "assigned_staff": len(assignments) if has_solution else None,
              "total_travel_minutes": sum(a["travel_minutes"] for a in assignments) if has_solution else None,
              "excluded_candidates": exclusions,
              "objective_order": ["maximize_filled_positions", "minimize_round_trip_travel"],
              "warnings": ["Source staffing and readiness/qualification flags require trusted backend verification.",
                           "One shared shift and one assignment per worker; no cross-role substitution or multi-shift rostering.",
                           "Existing source staffing deficits are preserved, not repaired. Incoming staff do not finance outgoing assignments.",
                           "Approval and atomic roster/availability rechecks are required; no staff are automatically reassigned."]}
    LOGGER.info("workforce_completed status=%s assignments=%d", result["status"], len(assignments))
    return result
