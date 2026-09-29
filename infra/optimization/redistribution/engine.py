"""Exact allocation for divisible quantities with linear per-unit transport costs.

Maximize fulfilled demand first, then minimize cost. This is NOT a vehicle
routing solver, batch selector, reservation system, or inventory mutation API.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from optimization.common.validation import (
    ValidationError,
    identifier,
    integer,
    nonnegative_number,
    object_fields,
)

LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = "1.0"
ALGORITHM_VERSION = "linear-cost-v1"


def recommend(
    request: dict[str, Any], policy: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate a snapshot and return a recommendation without changing inputs.

Each source represents one eligible batch at a distinct facility. safe_surplus
must already exclude reservations and protect the facility's safety stock.
The backend must revalidate and reserve inventory atomically after approval.
"""
    data = object_fields(
        request,
        required={
            "request_id", "inventory_snapshot_id", "shortage_facility",
            "medicine_id", "quantity_unit", "required_quantity", "candidate_sources",
        },
        optional=set(),
        path="request",
    )
    rules = object_fields(
        {} if policy is None else policy,
        required=set(),
        optional={"min_expiry_days"},
        path="policy",
    )
    min_expiry = integer(rules.get("min_expiry_days", 1), "policy.min_expiry_days", 1)
    request_id = identifier(data["request_id"], "request.request_id")
    snapshot_id = identifier(data["inventory_snapshot_id"], "request.inventory_snapshot_id")
    destination = identifier(data["shortage_facility"], "request.shortage_facility")
    medicine = identifier(data["medicine_id"], "request.medicine_id")
    unit = identifier(data["quantity_unit"], "request.quantity_unit")
    required = integer(data["required_quantity"], "request.required_quantity")
    if not isinstance(data["candidate_sources"], list):
        raise ValidationError("request.candidate_sources must be an array")

    eligible = []
    excluded = []
    seen_facilities: set[str] = set()
    # Validate every candidate even if the demand is zero or already satisfiable.
    for index, value in enumerate(data["candidate_sources"]):
        path = f"request.candidate_sources[{index}]"
        source = object_fields(
            value,
            required={
                "facility_id", "batch_id", "safe_surplus", "distance_km",
                "expiry_days", "transport_cost_per_unit_paise",
            },
            optional=set(),
            path=path,
        )
        facility = identifier(source["facility_id"], f"{path}.facility_id")
        batch = identifier(source["batch_id"], f"{path}.batch_id")
        surplus = integer(source["safe_surplus"], f"{path}.safe_surplus")
        expiry = integer(source["expiry_days"], f"{path}.expiry_days", None)
        distance = nonnegative_number(source["distance_km"], f"{path}.distance_km")
        cost = integer(
            source["transport_cost_per_unit_paise"],
            f"{path}.transport_cost_per_unit_paise",
        )
        if facility in seen_facilities:
            raise ValidationError(
                f"{path}.facility_id is duplicated; v1 accepts one batch per source facility"
            )
        seen_facilities.add(facility)
        reasons = []
        if facility == destination:
            reasons.append("same_as_destination")
        if expiry < min_expiry:
            reasons.append("insufficient_remaining_shelf_life")
        if surplus == 0:
            reasons.append("no_safe_surplus")
        if reasons:
            excluded.append({"facility_id": facility, "batch_id": batch, "reasons": reasons})
        else:
            eligible.append({
                "facility_id": facility, "batch_id": batch, "safe_surplus": surplus,
                "distance_km": distance, "transport_cost_per_unit_paise": cost,
            })

    # With linear unit costs and no fixed/route costs, cheapest-first allocation
    # is optimal: replacing an expensive unit with an available cheaper unit
    # preserves fulfillment and cannot increase cost.
    eligible.sort(key=lambda item: (
        item["transport_cost_per_unit_paise"], item["distance_km"], item["facility_id"]
    ))
    remaining = required
    transfers = []
    for source in eligible:
        if remaining == 0:
            break
        quantity = min(source["safe_surplus"], remaining)
        transfers.append({
            "source": source["facility_id"],
            "destination": destination,
            "batch_id": source["batch_id"],
            "medicine_id": medicine,
            "quantity": quantity,
            "quantity_unit": unit,
            "distance_km": source["distance_km"],
            "transport_cost_per_unit_paise": source["transport_cost_per_unit_paise"],
            "estimated_transport_cost_paise": quantity * source["transport_cost_per_unit_paise"],
            "reason": "Eligible safe surplus, selected in ascending per-unit transport cost order",
        })
        remaining -= quantity

    fulfilled = required - remaining
    status = "fulfilled" if remaining == 0 else ("partial" if fulfilled else "unavailable")
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "recommendation_id": str(uuid4()),
        "request_id": request_id,
        "inventory_snapshot_id": snapshot_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommendation_only": True,
        "approval_required": True,
        "status": status,
        "solver_status": "optimal_for_supported_model",
        "medicine_id": medicine,
        "quantity_unit": unit,
        "required_quantity": required,
        "fulfilled_quantity": fulfilled,
        "unresolved_shortage": remaining,
        "estimated_transport_cost_paise": sum(
            transfer["estimated_transport_cost_paise"] for transfer in transfers
        ),
        "recommended_transfers": transfers,
        "excluded_sources": excluded,
        "policy": {"min_expiry_days": min_expiry},
        "objective_order": ["maximize_fulfilled_quantity", "minimize_linear_transport_cost"],
        "warnings": [
            "Recommendation uses the supplied inventory snapshot; approval and atomic availability recheck are required.",
            "Fixed dispatch costs, road feasibility, vehicle capacity, and delivery time windows are not modeled.",
        ],
    }
    if remaining:
        result["warnings"].append("Eligible safe surplus is insufficient to meet the requested quantity.")
    LOGGER.info(
        "redistribution_completed status=%s candidates=%d transfers=%d",
        status, len(data["candidate_sources"]), len(transfers),
    )
    return result

