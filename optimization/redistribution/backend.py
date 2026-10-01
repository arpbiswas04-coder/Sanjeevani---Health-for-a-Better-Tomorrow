"""Read-only adapter for Member 2's serialized inventory records.

No HTTP server or database access. The trusted backend supplies a complete,
consistent snapshot plus operational inputs absent from its current schema.
"""

from datetime import date, datetime, timezone

from optimization.common.validation import ValidationError, identifier, integer, object_fields
from optimization.redistribution import recommend


def _utc_timestamp(value, path):
    if not isinstance(value, str):
        raise ValidationError(f"{path} must be an ISO timestamp with a timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{path} must be an ISO timestamp with a timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{path} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _record(value, fields, path):
    # Backend records also carry created_at/updated_at and display metadata.
    if not isinstance(value, dict) or not fields.issubset(value):
        raise ValidationError(f"{path} is missing required backend record fields")
    return value


def recommend_from_inventory(snapshot, policy=None, *, max_age_seconds=300, now=None):
    """V1: recommend from one explicitly selected batch per source facility."""
    return _recommend_from_inventory(snapshot, policy, max_age_seconds=max_age_seconds, now=now)


def recommend_all_batches(snapshot, policy=None, *, max_age_seconds=300, now=None):
    """V2: use all eligible batches, sharing one safety-stock cap per facility.

    Omit selected_batch_id from sources. Minimize linear facility-level unit
    costs after maximizing fulfillment; allocate earliest-expiring eligible
    batches first within each selected facility. No inventory is mutated.
    """
    return _recommend_from_inventory(
        snapshot, policy, max_age_seconds=max_age_seconds, now=now, all_batches=True
    )


def _recommend_from_inventory(snapshot, policy=None, *, max_age_seconds=300, now=None, all_batches=False):
    """Return Member 2's {success, data} envelope from serialized backend data.

All sources must be complete, consistently captured inventory snapshots.
Reservations must explicitly cover every row; no implicit zero reservations.
The v1 API retains its caller-selected batch restriction.
"""
    data = object_fields(
        snapshot,
        required={"request_id", "inventory_snapshot_id", "captured_at", "destination",
                  "medicine", "required_quantity", "sources"},
        optional=set(), path="snapshot",
    )
    integer(max_age_seconds, "max_age_seconds", 1)
    captured = _utc_timestamp(data["captured_at"], "snapshot.captured_at")
    current = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(current, datetime) or current.tzinfo is None or current.utcoffset() is None:
        raise ValidationError("now must be a timezone-aware datetime")
    current = current.astimezone(timezone.utc)
    age = (current - captured).total_seconds()
    if age < 0 or age > max_age_seconds:
        raise ValidationError("Inventory snapshot is future-dated or stale; refresh it")
    rules = object_fields({} if policy is None else policy, required=set(),
                          optional={"min_expiry_days"}, path="policy")
    min_expiry = integer(rules.get("min_expiry_days", 1), "policy.min_expiry_days", 1)
    destination = _record(data["destination"], {"id", "active"}, "destination")
    destination_id = identifier(destination["id"], "destination.id")
    if destination["active"] is not True:
        raise ValidationError("Destination facility must be active")
    medicine = _record(data["medicine"], {"id", "unit"}, "medicine")
    medicine_id = identifier(medicine["id"], "medicine.id")
    unit = identifier(medicine["unit"], "medicine.unit")
    if not isinstance(data["sources"], list):
        raise ValidationError("snapshot.sources must be an array")

    candidates, exclusions, calculations = [], [], []
    facility_batches = {}
    for index, item in enumerate(data["sources"]):
        path = f"sources[{index}]"
        source = object_fields(item, required={
            "facility", "inventory", "inventory_complete",
            "safety_stock", "reserved_quantities", "distance_km",
            "transport_cost_per_unit_paise",
        } | (set() if all_batches else {"selected_batch_id"}), optional=set(), path=path)
        facility = _record(source["facility"], {"id", "active"}, f"{path}.facility")
        facility_id = identifier(facility["id"], f"{path}.facility.id")
        if type(facility["active"]) is not bool:
            raise ValidationError(f"{path}.facility.active must be boolean")
        if source["inventory_complete"] is not True:
            raise ValidationError(f"{path} requires a complete inventory snapshot, not one API page")
        safety = integer(source["safety_stock"], f"{path}.safety_stock")
        selected_id = (
            "__facility_pool__" if all_batches
            else identifier(source["selected_batch_id"], f"{path}.selected_batch_id")
        )
        rows = source["inventory"]
        reservations = source["reserved_quantities"]
        if not isinstance(rows, list) or not isinstance(reservations, dict):
            raise ValidationError(f"{path} requires inventory array and reserved_quantities object")
        seen_rows, seen_batches = set(), set()
        usable_total, selected_available, selected_expiry = 0, None, None
        eligible_batches = []
        for row_index, value in enumerate(rows):
            row_path = f"{path}.inventory[{row_index}]"
            row = _record(value, {"id", "facility_id", "batch_id", "quantity", "batch"}, row_path)
            row_id = identifier(row["id"], f"{row_path}.id")
            batch_id = identifier(row["batch_id"], f"{row_path}.batch_id")
            if row_id in seen_rows or batch_id in seen_batches:
                raise ValidationError(f"{path} contains duplicate inventory or batch rows")
            seen_rows.add(row_id)
            seen_batches.add(batch_id)
            if row["facility_id"] != facility_id:
                raise ValidationError(f"{row_path} belongs to a different facility")
            quantity = integer(row["quantity"], f"{row_path}.quantity")
            if row_id not in reservations:
                raise ValidationError(f"{row_path} requires an explicit reservation quantity")
            reserved = integer(reservations[row_id], f"{row_path}.reserved_quantity")
            if reserved > quantity:
                raise ValidationError(f"{row_path} reservations exceed stock")
            batch = _record(row["batch"], {"id", "medicine_id", "expires_on", "recalled"}, f"{row_path}.batch")
            if batch["id"] != batch_id:
                raise ValidationError(f"{row_path} batch reference does not match")
            identifier(batch["medicine_id"], f"{row_path}.batch.medicine_id")
            if type(batch["recalled"]) is not bool:
                raise ValidationError(f"{row_path}.batch.recalled must be boolean")
            try:
                expiry = date.fromisoformat(batch["expires_on"])
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"{row_path}.batch.expires_on must be an ISO date") from exc
            # Use today's UTC date, not the snapshot date, including midnight rollover.
            expiry_days = (expiry - current.date()).days
            reasons = []
            if not facility["active"]:
                reasons.append("inactive_facility")
            if batch["medicine_id"] != medicine_id:
                reasons.append("different_medicine")
            if batch["recalled"]:
                reasons.append("recalled_batch")
            if expiry_days < min_expiry:
                reasons.append("insufficient_remaining_shelf_life")
            available = 0 if reasons else quantity - reserved
            usable_total += available
            if available:
                eligible_batches.append({"batch_id": batch_id, "inventory_id": row_id,
                                         "available": available, "expiry_days": expiry_days})
            if reasons:
                exclusions.append({"inventory_id": row_id, "reasons": reasons})
            if batch_id == selected_id:
                selected_available, selected_expiry = available, expiry_days
        if set(reservations) != seen_rows:
            raise ValidationError(f"{path}.reserved_quantities contains unknown inventory IDs")
        if not all_batches and selected_available is None:
            raise ValidationError(f"{path}.selected_batch_id is not present in inventory")
        safe_surplus = max(0, usable_total - safety)
        if all_batches:
            # Aggregate only for facility selection. Expand back to real batch
            # IDs before returning any recommendation to the caller.
            selected_expiry = min((b["expiry_days"] for b in eligible_batches), default=min_expiry)
            facility_batches[facility_id] = sorted(
                eligible_batches, key=lambda batch: (batch["expiry_days"], batch["batch_id"])
            )
        else:
            safe_surplus = min(selected_available, safe_surplus)
        candidates.append({
            "facility_id": facility_id, "batch_id": selected_id,
            "safe_surplus": safe_surplus, "expiry_days": selected_expiry,
            "distance_km": source["distance_km"],
            "transport_cost_per_unit_paise": source["transport_cost_per_unit_paise"],
        })
        calculation = {"facility_id": facility_id, "eligible_unreserved_quantity": usable_total,
                       "safety_stock": safety, "safe_surplus": safe_surplus}
        if all_batches:
            calculation["eligible_batch_count"] = len(eligible_batches)
        else:
            calculation["selected_batch_available"] = selected_available
        calculations.append(calculation)

    result = recommend({
        "request_id": data["request_id"], "inventory_snapshot_id": data["inventory_snapshot_id"],
        "shortage_facility": destination_id, "medicine_id": medicine_id,
        "quantity_unit": unit, "required_quantity": data["required_quantity"],
        "candidate_sources": candidates,
    }, rules)
    result["inventory_captured_at"] = captured.isoformat()
    result["inventory_evaluated_at"] = current.isoformat()
    result["snapshot_exclusions"] = exclusions
    result["surplus_calculations"] = calculations
    if all_batches:
        transfers = []
        for allocation in result["recommended_transfers"]:
            remaining = allocation["quantity"]
            for batch in facility_batches[allocation["source"]]:
                quantity = min(remaining, batch["available"])
                if quantity == 0:
                    break
                transfers.append({
                    **allocation, "batch_id": batch["batch_id"],
                    "inventory_id": batch["inventory_id"], "quantity": quantity,
                    "expiry_days": batch["expiry_days"],
                    "estimated_transport_cost_paise": quantity * allocation["transport_cost_per_unit_paise"],
                    "reason": "Lowest linear-cost facility allocation; earliest eligible expiry first within facility",
                })
                remaining -= quantity
            if remaining:
                raise RuntimeError("Batch expansion failed to conserve allocated quantity")
        # Facility-level exclusions must not expose an internal aggregate batch ID.
        result["excluded_sources"] = [
            {"facility_id": source["facility_id"], "reasons": source["reasons"]}
            for source in result["excluded_sources"]
        ]
        result["recommended_transfers"] = transfers
        result["schema_version"] = "2.0"
        result["algorithm_version"] = "facility-linear-fefo-v2"
        result["batch_selection"] = "earliest_expiry_within_facility"
    else:
        result["warnings"].append(
            "Only caller-selected batches were considered. Other eligible batches may satisfy additional demand."
        )
    return {"success": True, "data": result}
