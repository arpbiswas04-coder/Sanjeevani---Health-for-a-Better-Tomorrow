"""Single-medicine, single-destination procurement with indivisible packs."""

import logging
import time
from datetime import timedelta
from uuid import uuid4

from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

LOGGER = logging.getLogger(__name__)


def _bounded(value, path, maximum=1_000_000, minimum=0):
    result = integer(value, path, minimum)
    if result > maximum: raise ValidationError(f"{path} exceeds {maximum}")
    return result


def _solve(cp, model, seconds):
    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    return solver, solver.solve(model)


from optimization.common.telemetry import measured


@measured("optimizer", "procurement")
def recommend_procurement(request, *, max_age_seconds=3600, time_limit_seconds=5, now=None):
    """Maximize shortage coverage, then minimize cost, then surplus units.

    All prices are integer INR paise, inclusive of applicable costs except the
    separately declared fixed delivery fee. Quotes are for this destination.
    One quote per supplier, one medicine, and one proposed order per supplier.
    """
    current = utc_now(now)
    age = _bounded(max_age_seconds, "max_age_seconds", 86400, 1)
    seconds = nonnegative_number(time_limit_seconds, "time_limit_seconds")
    if not 0 < seconds <= 60: raise ValidationError("time_limit_seconds must be in (0, 60]")
    data = object_fields(request, required={"request_id", "shortage_snapshot_id", "captured_at", "destination",
        "medicine_id", "quantity_unit", "required_quantity", "max_overstock_units", "budget_paise",
        "max_lead_time_days", "min_shelf_life_days_on_arrival", "offers"}, optional=set(), path="request")
    ids = {key: identifier(data[key], key) for key in
           ("request_id", "shortage_snapshot_id", "destination", "medicine_id", "quantity_unit")}
    captured = utc_timestamp(data["captured_at"], "captured_at")
    if not 0 <= (current - captured).total_seconds() < age:
        raise ValidationError("Shortage snapshot is stale or future-dated")
    required = _bounded(data["required_quantity"], "required_quantity")
    overstock = _bounded(data["max_overstock_units"], "max_overstock_units")
    budget = _bounded(data["budget_paise"], "budget_paise", 1_000_000_000_000)
    lead_limit = _bounded(data["max_lead_time_days"], "max_lead_time_days", 3650)
    shelf_limit = _bounded(data["min_shelf_life_days_on_arrival"], "min_shelf_life_days_on_arrival", 3650, 1)
    if not isinstance(data["offers"], list) or len(data["offers"]) > 500:
        raise ValidationError("offers must contain at most 500 quotes")
    eligible, excluded, seen = {}, [], set()
    for index, raw in enumerate(data["offers"]):
        path = f"offers[{index}]"
        offer = object_fields(raw, required={"supplier_id", "quote_id", "approved", "medicine_id", "quantity_unit",
            "pack_size", "available_packs", "minimum_order_packs", "price_per_pack_paise", "delivery_fee_paise",
            "lead_time_days", "shelf_life_days_on_arrival", "observed_at", "valid_until"}, optional=set(), path=path)
        supplier = identifier(offer["supplier_id"], f"{path}.supplier_id")
        if supplier in seen: raise ValidationError("Only one quote per supplier is supported")
        seen.add(supplier)
        quote = identifier(offer["quote_id"], f"{path}.quote_id")
        medicine = identifier(offer["medicine_id"], f"{path}.medicine_id")
        unit = identifier(offer["quantity_unit"], f"{path}.quantity_unit")
        if type(offer["approved"]) is not bool: raise ValidationError(f"{path}.approved must be boolean")
        pack = _bounded(offer["pack_size"], f"{path}.pack_size", minimum=1)
        available = _bounded(offer["available_packs"], f"{path}.available_packs")
        minimum = _bounded(offer["minimum_order_packs"], f"{path}.minimum_order_packs", minimum=1)
        price = _bounded(offer["price_per_pack_paise"], f"{path}.price_per_pack_paise", 1_000_000_000)
        fee = _bounded(offer["delivery_fee_paise"], f"{path}.delivery_fee_paise", 1_000_000_000)
        lead = _bounded(offer["lead_time_days"], f"{path}.lead_time_days", 3650)
        shelf = _bounded(offer["shelf_life_days_on_arrival"], f"{path}.shelf_life_days_on_arrival", 3650)
        observed = utc_timestamp(offer["observed_at"], f"{path}.observed_at")
        expires = utc_timestamp(offer["valid_until"], f"{path}.valid_until")
        if expires <= observed: raise ValidationError(f"{path} quote expiry must follow observation")
        reasons = []
        if not offer["approved"]: reasons.append("supplier_not_approved")
        if medicine != ids["medicine_id"] or unit != ids["quantity_unit"]: reasons.append("medicine_or_unit_mismatch")
        if lead > lead_limit: reasons.append("delivery_too_late")
        if shelf < shelf_limit: reasons.append("insufficient_shelf_life_on_arrival")
        if observed > captured: reasons.append("quote_observation_after_snapshot")
        elif (current - observed).total_seconds() >= age: reasons.append("stale_quote")
        if expires <= current: reasons.append("expired_quote")
        # Zero shortage must never create an order, even with allowed overstock.
        cap = min(available, (required + overstock) // pack) if required else 0
        if cap < minimum: reasons.append("minimum_order_exceeds_stock_or_quantity_limit")
        if minimum * price + fee > budget: reasons.append("minimum_order_exceeds_budget")
        if reasons:
            excluded.append({"supplier_id": supplier, "quote_id": quote, "reasons": reasons})
        else:
            eligible[supplier] = {"quote_id": quote, "pack_size": pack, "capacity": cap, "minimum": minimum,
                                  "price": price, "fee": fee, "lead_time_days": lead,
                                  "valid_until": min(expires, observed + timedelta(seconds=age))}
    try:
        from ortools.sat.python import cp_model as cp
    except ImportError as exc:
        raise RuntimeError("Procurement requires the infra[transport] extra") from exc
    model = cp.CpModel()
    variables, quantity_terms, cost_terms = {}, [], []
    for i, (supplier, offer) in enumerate(sorted(eligible.items())):
        packs = model.new_int_var(0, offer["capacity"], f"packs_{i}")
        active = model.new_bool_var(f"order_{i}")
        model.add(packs <= offer["capacity"] * active)
        model.add(packs >= offer["minimum"] * active)
        variables[supplier] = packs
        quantity_terms.append(packs * offer["pack_size"])
        cost_terms.extend([packs * offer["price"], active * offer["fee"]])
    total, cost = sum(quantity_terms), sum(cost_terms)
    model.add(total <= required + overstock)
    model.add(cost <= budget)
    covered = model.new_int_var(0, required, "covered_units")
    model.add_min_equality(covered, [required, total])
    objectives = [("maximize_shortage_coverage", covered, True), ("minimize_purchase_cost", cost, False),
                  ("minimize_purchased_units", total, False)]
    allocation, phases, proven = None, [], []
    started = time.monotonic()
    for name, expression, maximize in objectives:
        remaining = seconds - (time.monotonic() - started)
        if remaining <= 0: break
        if maximize: model.maximize(expression)
        else: model.minimize(expression)
        if model.validate(): raise RuntimeError("Procurement model validation failed")
        solver, status = _solve(cp, model, remaining)
        phases.append({"objective": name, "status": solver.status_name(status)})
        if status not in (cp.OPTIMAL, cp.FEASIBLE): break
        allocation = {supplier: solver.value(var) for supplier, var in variables.items()}
        if status != cp.OPTIMAL: break
        proven.append(name)
        model.add(expression == solver.value(expression))
        model.clear_hints()
        for supplier, var in variables.items(): model.add_hint(var, allocation[supplier])
    has_solution = allocation is not None
    orders, expiries = [], [captured + timedelta(seconds=age)]
    for supplier, packs in sorted((allocation or {}).items()):
        if not packs: continue
        offer = eligible[supplier]
        orders.append({"supplier_id": supplier, "quote_id": offer["quote_id"], "packs": packs,
                       "pack_size": offer["pack_size"], "quantity": packs * offer["pack_size"],
                       "price_per_pack_paise": offer["price"], "delivery_fee_paise": offer["fee"],
                       "total_cost_paise": packs * offer["price"] + offer["fee"], "lead_time_days": offer["lead_time_days"]})
        expiries.append(offer["valid_until"])
    bought = sum(o["quantity"] for o in orders) if has_solution else None
    spent = sum(o["total_cost_paise"] for o in orders) if has_solution else None
    expiry = min(expiries)
    finished = utc_now() if now is None else current
    result = {**ids, "schema_version": "procurement-1.0", "recommendation_id": str(uuid4()),
              "generated_at": current.isoformat(), "valid_until": expiry.isoformat(),
              "recommendation_only": True, "approval_required": True, "has_solution": has_solution,
              "status": "expired_during_computation" if finished >= expiry else ("recommended" if has_solution else "no_solution"),
              "solver_status": "optimal" if len(proven) == 3 else ("feasible" if has_solution else "no_solution"),
              "phases": phases, "proven_objectives": proven, "recommended_orders": orders,
              "required_quantity": required, "purchased_quantity": bought,
              "covered_quantity": min(required, bought) if has_solution else None,
              "unresolved_shortage": max(0, required - bought) if has_solution else None,
              "overstock_units": max(0, bought - required) if has_solution else None,
              "total_cost_paise": spent, "remaining_budget_paise": budget - spent if has_solution else None,
              "excluded_offers": excluded, "policy": {"budget_paise": budget, "max_overstock_units": overstock,
                  "max_lead_time_days": lead_limit, "min_shelf_life_days_on_arrival": shelf_limit, "max_age_seconds": age},
              "warnings": ["Prices, supplier approval, stock and delivery/shelf-life promises require backend verification.",
                           "Use the remaining shortage after approved/reserved redistribution; do not double-count proposed transfers.",
                           "One medicine and destination, one quote/order per supplier. No shared multi-item shipping or discounts.",
                           "Authorized approval, budget reservation and supplier reconfirmation are required; no purchase order is submitted."]}
    LOGGER.info("procurement_completed status=%s orders=%d", result["status"], len(orders))
    return result
