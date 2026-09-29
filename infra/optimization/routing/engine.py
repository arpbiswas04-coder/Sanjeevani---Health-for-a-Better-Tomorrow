"""OR-Tools Routing recommendations; never dispatches a vehicle."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

LOGGER = logging.getLogger(__name__)
MAX_MINUTES = 10080


def _window(value, path):
    if not isinstance(value, list) or len(value) != 2:
        raise ValidationError(f"{path} must be [opening_minute, closing_minute]")
    start, end = [integer(v, path) for v in value]
    if not start <= end <= MAX_MINUTES:
        raise ValidationError(f"{path} must be ordered and within 0..{MAX_MINUTES}")
    return start, end


def _bounded(value, path, maximum, minimum=0):
    result = integer(value, path, minimum)
    if result > maximum:
        raise ValidationError(f"{path} exceeds {maximum}")
    return result


def _matrix(value, size, path, maximum):
    if not isinstance(value, list) or len(value) != size:
        raise ValidationError(f"{path} must match location_ids")
    result = []
    for i, row in enumerate(value):
        if not isinstance(row, list) or len(row) != size:
            raise ValidationError(f"{path} must be square")
        result.append([_bounded(v, f"{path}[{i}][{j}]", maximum) for j, v in enumerate(row)])
        if result[-1][i] != 0:
            raise ValidationError(f"{path} diagonal must be zero")
    return result


def _solve(routing, parameters):
    return routing.SolveWithParameters(parameters)


def recommend_routes(request, *, time_limit_seconds=3):
    """Route unsplittable deliveries from one depot, returning to that depot.

    Time values are integer minutes from a caller-defined planning origin.
    All delivery quantities and vehicle capacities use one common load unit.
    Objective: maximize delivered units, then minimize travel + service minutes.
    The search may return a feasible result without proving this objective.
    """
    seconds = nonnegative_number(time_limit_seconds, "time_limit_seconds")
    if not 0 < seconds <= 60:
        raise ValidationError("time_limit_seconds must be greater than zero and at most 60")
    data = object_fields(request, required={"request_id", "travel_snapshot_id", "quantity_unit",
                         "depot", "stops", "vehicles", "location_ids", "travel_time_minutes", "distance_meters"},
                         optional=set(), path="request")
    ids = {key: identifier(data[key], key) for key in ("request_id", "travel_snapshot_id", "quantity_unit")}
    depot = object_fields(data["depot"], required={"facility_id", "window"}, optional=set(), path="depot")
    depot_id = identifier(depot["facility_id"], "depot.facility_id")
    depot_window = _window(depot["window"], "depot.window")
    if not isinstance(data["stops"], list) or len(data["stops"]) > 200:
        raise ValidationError("stops must be an array of at most 200 deliveries")
    if not isinstance(data["vehicles"], list) or not 1 <= len(data["vehicles"]) <= 50:
        raise ValidationError("vehicles must contain 1..50 vehicles")
    stops, vehicles, seen = [], [], {depot_id}
    for i, raw in enumerate(data["stops"]):
        path = f"stops[{i}]"
        stop = object_fields(raw, required={"facility_id", "quantity", "service_minutes", "window"}, optional=set(), path=path)
        facility = identifier(stop["facility_id"], f"{path}.facility_id")
        if facility in seen:
            raise ValidationError("Stop IDs must be unique and different from the depot")
        seen.add(facility)
        window = _window(stop["window"], f"{path}.window")
        service = _bounded(stop["service_minutes"], f"{path}.service_minutes", MAX_MINUTES)
        if service > window[1] - window[0]:
            raise ValidationError(f"{path} service duration exceeds the delivery window")
        stops.append({"facility_id": facility, "quantity": _bounded(stop["quantity"], f"{path}.quantity", 1_000_000, 1),
                      "service_minutes": service, "window": window})
    vehicle_ids = set()
    for i, raw in enumerate(data["vehicles"]):
        path = f"vehicles[{i}]"
        vehicle = object_fields(raw, required={"vehicle_id", "capacity", "shift"}, optional=set(), path=path)
        vehicle_id = identifier(vehicle["vehicle_id"], f"{path}.vehicle_id")
        if vehicle_id in vehicle_ids:
            raise ValidationError("Vehicle IDs must be unique")
        vehicle_ids.add(vehicle_id)
        shift = _window(vehicle["shift"], f"{path}.shift")
        window = (max(shift[0], depot_window[0]), min(shift[1], depot_window[1]))
        if window[0] > window[1]:
            raise ValidationError(f"{path} shift must overlap the depot window")
        vehicles.append({"vehicle_id": vehicle_id, "capacity": _bounded(vehicle["capacity"], f"{path}.capacity", 1_000_000, 1),
                         "window": window})
    location_ids = [depot_id] + [s["facility_id"] for s in stops]
    if data["location_ids"] != location_ids:
        raise ValidationError("location_ids must contain depot then stops in their declared order")
    size = len(location_ids)
    travel = _matrix(data["travel_time_minutes"], size, "travel_time_minutes", MAX_MINUTES)
    distances = _matrix(data["distance_meters"], size, "distance_meters", 1_000_000_000)
    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError as exc:
        raise RuntimeError('Routing requires OR-Tools; install infra with the [transport] extra') from exc
    manager = pywrapcp.RoutingIndexManager(size, len(vehicles), 0)
    routing = pywrapcp.RoutingModel(manager)
    service = [0] + [s["service_minutes"] for s in stops]
    quantities = [0] + [s["quantity"] for s in stops]

    def transit(a, b):
        source, destination = manager.IndexToNode(a), manager.IndexToNode(b)
        return service[source] + travel[source][destination]

    transit_id = routing.RegisterTransitCallback(transit)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_id)
    routing.AddDimension(transit_id, MAX_MINUTES, MAX_MINUTES, False, "Time")
    times = routing.GetDimensionOrDie("Time")
    demand_id = routing.RegisterUnaryTransitCallback(lambda index: quantities[manager.IndexToNode(index)])
    routing.AddDimensionWithVehicleCapacity(demand_id, 0, [v["capacity"] for v in vehicles], True, "Capacity")
    # Every feasible route's travel + service is bounded by its shift span.
    # Thus one extra delivered unit dominates any possible time-cost change.
    penalty_per_unit = 1 + sum(v["window"][1] - v["window"][0] for v in vehicles)
    for node, stop in enumerate(stops, start=1):
        index = manager.NodeToIndex(node)
        times.CumulVar(index).SetRange(stop["window"][0], stop["window"][1] - stop["service_minutes"])
        routing.AddDisjunction([index], penalty_per_unit * stop["quantity"])
        routing.AddVariableMinimizedByFinalizer(times.CumulVar(index))
    for i, vehicle in enumerate(vehicles):
        for index in (routing.Start(i), routing.End(i)):
            times.CumulVar(index).SetRange(*vehicle["window"])
            routing.AddVariableMinimizedByFinalizer(times.CumulVar(index))
    parameters = pywrapcp.DefaultRoutingSearchParameters()
    parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    parameters.time_limit.FromMilliseconds(max(1, int(seconds * 1000)))
    solution = _solve(routing, parameters)
    status_names = {0: "not_solved", 1: "success", 2: "partial_success", 3: "fail",
                    4: "timeout", 5: "invalid", 6: "infeasible", 7: "optimal"}
    status_code = routing.status()
    has_solution = solution is not None
    routes, served, unserved = [], set(), []
    if has_solution:
        for vehicle_index, vehicle in enumerate(vehicles):
            index = routing.Start(vehicle_index)
            next_index = solution.Value(routing.NextVar(index))
            if routing.IsEnd(next_index):
                continue
            departure = solution.Value(times.CumulVar(index))
            visits, legs, load = [], [], 0
            while not routing.IsEnd(index):
                nxt = solution.Value(routing.NextVar(index))
                a, b = manager.IndexToNode(index), manager.IndexToNode(nxt)
                leave = solution.Value(times.CumulVar(index)) + service[a]
                reach = leave + travel[a][b]
                scheduled = solution.Value(times.CumulVar(nxt))
                legs.append({"from": location_ids[a], "to": location_ids[b],
                             "travel_minutes": travel[a][b], "distance_meters": distances[a][b],
                             "waiting_minutes": scheduled - reach})
                if not routing.IsEnd(nxt):
                    stop = stops[b - 1]
                    served.add(b)
                    load += stop["quantity"]
                    visits.append({"facility_id": stop["facility_id"], "quantity": stop["quantity"],
                                   "earliest_arrival_minute": reach, "service_start_minute": scheduled,
                                   "service_end_minute": scheduled + service[b]})
                index = nxt
            end = solution.Value(times.CumulVar(index))
            routes.append({"vehicle_id": vehicle["vehicle_id"], "depot": depot_id,
                           "departure_minute": departure, "return_minute": end,
                           "duration_minutes": end - departure, "quantity": load,
                           "capacity": vehicle["capacity"], "stops": visits, "legs": legs,
                           "travel_minutes": sum(l["travel_minutes"] for l in legs),
                           "distance_meters": sum(l["distance_meters"] for l in legs),
                           "waiting_minutes": sum(l["waiting_minutes"] for l in legs),
                           "service_minutes": sum(v["service_end_minute"] - v["service_start_minute"] for v in visits)})
        for node, stop in enumerate(stops, start=1):
            if node not in served:
                unserved.append({"facility_id": stop["facility_id"], "quantity": stop["quantity"],
                                 "reason": "not_in_returned_plan"})
    fulfilled = sum(r["quantity"] for r in routes) if has_solution else None
    required = sum(quantities)
    result = {**ids, "schema_version": "routing-1.0", "algorithm_version": "ortools-cvrptw-v1",
              "recommendation_id": str(uuid4()), "generated_at": datetime.now(timezone.utc).isoformat(),
              "recommendation_only": True, "approval_required": True, "has_solution": has_solution,
              "solver_status": status_names.get(status_code, "unknown"), "optimality_proven": status_code == 7 and has_solution,
              "status": ("fulfilled" if fulfilled == required else ("partial" if fulfilled else "unavailable")) if has_solution else "not_computed",
              "required_quantity": required, "fulfilled_quantity": fulfilled,
              "unresolved_quantity": required - fulfilled if has_solution else None,
              "routes": routes, "unserved_stops": unserved if has_solution else None,
              "total_distance_meters": sum(r["distance_meters"] for r in routes) if has_solution else None,
              "total_travel_minutes": sum(r["travel_minutes"] for r in routes) if has_solution else None,
              "time_limit_seconds": seconds, "objective_order": ["maximize_delivered_units", "minimize_travel_plus_service_minutes"],
              "warnings": [
                  "A feasible plan is not necessarily optimal. Unserved stops are not proof of infeasibility.",
                  "One depot, one trip per vehicle, indivisible deliveries and a common load unit are assumed.",
                  "Travel data, cargo compatibility, authorization and current vehicle availability require backend validation.",
                  "This routing plan does not reserve inventory or vehicles and does not dispatch them.",
              ]}
    LOGGER.info("routing_completed status=%s vehicles_used=%d", result["solver_status"], len(routes))
    return result
