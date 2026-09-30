"""Two-stage CP-SAT allocation. No routing, approval, or inventory mutation."""

import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

LOGGER = logging.getLogger(__name__)


def _quantity(value, path):
    result = integer(value, path)
    if result > 1_000_000_000:
        raise ValidationError(f"{path} exceeds the supported limit of 1000000000")
    return result


def _array(value, path, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise ValidationError(f"{path} must be an array of at most {limit} entries")
    return value


def _solve(cp, model, seconds):
    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    return solver, solver.solve(model)


from optimization.common.telemetry import measured


@measured("optimizer", "transport")
def recommend_transport(request, *, time_limit_seconds=5, min_expiry_days=1, priority_weights=None):
    """Allocate one medicine to multiple destinations using trusted eligible stock.

    safe_surplus is a shared facility cap after reservations and safety stock.
    Batch available_quantity is already unreserved and otherwise eligible.
    Costs are per lane, identical across batches; absent lanes are prohibited.
    Optional integer priority weights insert an objective between maximum
    fulfillment and minimum cost; they never relax any feasibility constraint.
    """
    seconds = nonnegative_number(time_limit_seconds, "time_limit_seconds")
    if not 0 < seconds <= 60:
        raise ValidationError("time_limit_seconds must be greater than zero and at most 60")
    minimum = integer(min_expiry_days, "min_expiry_days", 1)
    data = object_fields(request, required={"request_id", "inventory_snapshot_id", "medicine_id",
                         "quantity_unit", "sources", "destinations", "lanes"}, optional=set(), path="request")
    ids = {key: identifier(data[key], key) for key in
           ("request_id", "inventory_snapshot_id", "medicine_id", "quantity_unit")}
    sources, destinations, lanes, excluded = {}, {}, {}, []
    for i, raw in enumerate(_array(data["sources"], "sources", 500)):
        path = f"sources[{i}]"
        source = object_fields(raw, required={"facility_id", "safe_surplus", "batches"}, optional=set(), path=path)
        facility = identifier(source["facility_id"], f"{path}.facility_id")
        if facility in sources:
            raise ValidationError("Duplicate source facility")
        cap = _quantity(source["safe_surplus"], f"{path}.safe_surplus")
        batches, seen = [], set()
        for j, raw_batch in enumerate(_array(source["batches"], f"{path}.batches", 1000)):
            batch_path = f"{path}.batches[{j}]"
            batch = object_fields(raw_batch, required={"batch_id", "available_quantity", "expiry_days"},
                                  optional=set(), path=batch_path)
            batch_id = identifier(batch["batch_id"], f"{batch_path}.batch_id")
            if batch_id in seen:
                raise ValidationError("Duplicate batch within source facility")
            seen.add(batch_id)
            available = _quantity(batch["available_quantity"], f"{batch_path}.available_quantity")
            expiry = integer(batch["expiry_days"], f"{batch_path}.expiry_days", None)
            if expiry < minimum or available == 0:
                excluded.append({"source": facility, "batch_id": batch_id,
                                 "reason": "insufficient_shelf_life" if expiry < minimum else "no_available_stock"})
            else:
                batches.append({"batch_id": batch_id, "available_quantity": available, "expiry_days": expiry})
        batches.sort(key=lambda b: (b["expiry_days"], b["batch_id"]))
        sources[facility] = {"capacity": min(cap, sum(b["available_quantity"] for b in batches)), "batches": batches}
    for i, raw in enumerate(_array(data["destinations"], "destinations", 500)):
        destination = object_fields(raw, required={"facility_id", "required_quantity"}, optional=set(), path=f"destinations[{i}]")
        facility = identifier(destination["facility_id"], f"destinations[{i}].facility_id")
        if facility in destinations or facility in sources:
            raise ValidationError("Destinations must be unique and separate from source facilities")
        destinations[facility] = _quantity(destination["required_quantity"], f"destinations[{i}].required_quantity")
    cost_bound = 0
    for i, raw in enumerate(_array(data["lanes"], "lanes", 2000)):
        path = f"lanes[{i}]"
        lane = object_fields(raw, required={"source", "destination", "capacity", "unit_cost_paise", "fixed_dispatch_cost_paise"},
                             optional=set(), path=path)
        key = (identifier(lane["source"], f"{path}.source"), identifier(lane["destination"], f"{path}.destination"))
        if key in lanes or key[0] not in sources or key[1] not in destinations:
            raise ValidationError("Lane is duplicated or references an unknown source/destination")
        cap = min(_quantity(lane["capacity"], f"{path}.capacity"), sources[key[0]]["capacity"], destinations[key[1]])
        unit = _quantity(lane["unit_cost_paise"], f"{path}.unit_cost_paise")
        fixed = _quantity(lane["fixed_dispatch_cost_paise"], f"{path}.fixed_dispatch_cost_paise")
        cost_bound += cap * unit + fixed
        lanes[key] = {"capacity": cap, "unit": unit, "fixed": fixed}
    if cost_bound > 2**60:
        raise ValidationError("Aggregate cost range exceeds safe solver integer bounds")
    priorities = None
    if priority_weights is not None:
        raw = object_fields(priority_weights, required=set(destinations), optional=set(), path="priority_weights")
        priorities = {facility: _quantity(raw[facility], f"priority_weights.{facility}") for facility in destinations}
        if any(weight > 1_000_000 for weight in priorities.values()):
            raise ValidationError("priority_weights must be at most 1000000")
        if sum(lane["capacity"] * priorities[key[1]] for key, lane in lanes.items()) > 2**60:
            raise ValidationError("Priority objective exceeds safe solver integer bounds")
    try:
        from ortools.sat.python import cp_model as cp
    except ImportError as exc:
        raise RuntimeError('Transport requires OR-Tools; install the infra package with the [transport] extra') from exc

    model = cp.CpModel()
    quantities, cost_terms = {}, []
    for index, (key, lane) in enumerate(sorted(lanes.items())):
        q = model.new_int_var(0, lane["capacity"], f"quantity_{index}")
        active = model.new_bool_var(f"dispatch_{index}")
        model.add(q <= lane["capacity"] * active)
        model.add(q >= active)
        quantities[key] = q
        cost_terms.extend([q * lane["unit"], active * lane["fixed"]])
    for facility, source in sources.items():
        model.add(sum(q for (s, _), q in quantities.items() if s == facility) <= source["capacity"])
    for facility, demand in destinations.items():
        model.add(sum(q for (_, d), q in quantities.items() if d == facility) <= demand)
    total = sum(quantities.values())
    objectives = [("maximize_fulfillment", total, True)]
    if priorities is not None:
        objectives.append(("maximize_priority_weighted_fulfillment",
                           sum(q * priorities[d] for (_, d), q in quantities.items()), True))
    objectives.append(("minimize_cost", sum(cost_terms), False))
    phases, proven = [], set()
    allocation = None
    started = time.monotonic()
    for objective_name, expression, maximize in objectives:
        remaining = seconds - (time.monotonic() - started)
        if remaining <= 0:
            break
        if maximize:
            model.maximize(expression)
        else:
            model.minimize(expression)
        if model.validate():
            raise RuntimeError("Transport model validation failed")
        solver, status = _solve(cp, model, remaining)
        phases.append({"objective": objective_name, "status": solver.status_name(status)})
        if status not in (cp.OPTIMAL, cp.FEASIBLE):
            break  # Preserve the previous incumbent if this phase has none.
        allocation = {key: solver.value(q) for key, q in quantities.items()}
        if status != cp.OPTIMAL:
            break  # Never optimize a later objective before proving this one.
        proven.add(objective_name)
        model.add(expression == solver.value(expression))
        model.clear_hints()
        for key, q in quantities.items():
            model.add_hint(q, allocation[key])
    fulfillment_proven = "maximize_fulfillment" in proven
    cost_proven = "minimize_cost" in proven
    has_solution = allocation is not None
    transfers, dispatches = [], []
    batch_remaining = {(s, b["batch_id"]): b["available_quantity"]
                       for s, source in sources.items() for b in source["batches"]}
    for (source, destination), quantity in sorted((allocation or {}).items()):
        if not quantity:
            continue
        lane = lanes[(source, destination)]
        dispatches.append({"source": source, "destination": destination, "quantity": quantity,
                           "fixed_dispatch_cost_paise": lane["fixed"],
                           "variable_cost_paise": quantity * lane["unit"],
                           "total_cost_paise": lane["fixed"] + quantity * lane["unit"]})
        remaining = quantity
        for batch in sources[source]["batches"]:
            key = (source, batch["batch_id"])
            take = min(remaining, batch_remaining[key])
            if take:
                transfers.append({"source": source, "destination": destination,
                                  "batch_id": batch["batch_id"], "quantity": take,
                                  "medicine_id": ids["medicine_id"], "quantity_unit": ids["quantity_unit"],
                                  "expiry_days": batch["expiry_days"]})
                batch_remaining[key] -= take
                remaining -= take
            if not remaining:
                break
        if remaining:
            raise RuntimeError("Transport batch expansion failed to conserve quantities")
    per_destination = []
    for destination, demand in sorted(destinations.items()):
        received = sum(q for (_, d), q in (allocation or {}).items() if d == destination) if has_solution else None
        per_destination.append({"facility_id": destination, "required_quantity": demand,
                                "fulfilled_quantity": received,
                                "unresolved_shortage": demand - received if has_solution else None})
    filled = sum((allocation or {}).values()) if has_solution else None
    demand = sum(destinations.values())
    result = {
        **ids, "schema_version": "transport-1.0", "algorithm_version": "cp-sat-fixed-lane-v1",
        "recommendation_id": str(uuid4()), "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommendation_only": True, "approval_required": True, "has_solution": has_solution,
        "solver_status": "optimal" if cost_proven else ("feasible" if has_solution else "no_solution"),
        "fulfillment_optimal": fulfillment_proven, "cost_optimal": cost_proven,
        "phases": phases, "time_limit_seconds": seconds,
        "status": ("fulfilled" if filled == demand else ("partial" if filled else "unavailable")) if has_solution else "not_computed",
        "required_quantity": demand, "fulfilled_quantity": filled,
        "unresolved_shortage": demand - filled if has_solution else None,
        "estimated_transport_cost_paise": sum(d["total_cost_paise"] for d in dispatches) if has_solution else None,
        "destinations": per_destination, "dispatches": dispatches,
        "recommended_transfers": transfers, "excluded_batches": excluded,
        "policy": {"min_expiry_days": minimum},
        "warnings": [
            "Trusted eligible stock and safe-surplus inputs require backend validation and atomic recheck after approval.",
            "Fixed cost is charged once per used source-destination lane; this is not a vehicle route or per-trip model.",
            "Equal-priority demand is optimized in aggregate; no fairness, emergency priority, or delivery time windows are modeled.",
        ],
    }
    if not cost_proven:
        result["warnings"].append("Full lexicographic optimality is not proven; inspect has_solution and phase statuses.")
    result["objective_order"] = [name for name, _, _ in objectives]
    if priorities is not None:
        result["schema_version"] = "transport-priority-1.0"
        result["algorithm_version"] = "cp-sat-priority-fixed-lane-v1"
        result["priority_weights"] = priorities
        result["priority_optimal"] = "maximize_priority_weighted_fulfillment" in proven
        result["priority_weighted_units"] = (
            sum(q * priorities[d] for (_, d), q in allocation.items()) if has_solution else None
        )
        result["warnings"][2] = "Priority is optimized only after total fulfillment; fairness and delivery time windows are not modeled."
    LOGGER.info("transport_completed status=%s lanes=%d transfers=%d", result["solver_status"], len(lanes), len(transfers))
    return result
