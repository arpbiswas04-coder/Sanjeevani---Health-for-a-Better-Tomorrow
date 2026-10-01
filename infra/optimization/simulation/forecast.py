"""Member 3 demand handoff; accepts explicit quantities, never guesses units."""
import copy
from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, object_fields
from optimization.simulation.timeline import run_timeline


def simulate_forecast(baseline, forecast, *, policy=None, now=None, max_age_seconds=86400):
    data = object_fields(forecast, required={"forecast_id", "model_version", "generated_at", "inventory_snapshot_id",
        "destination_id", "medicine_id", "quantity_unit", "periods"}, optional=set(), path="forecast")
    for field in ("forecast_id", "model_version", "inventory_snapshot_id", "destination_id", "medicine_id", "quantity_unit"):
        identifier(data[field], field)
    if not isinstance(baseline, dict): raise ValidationError("Baseline must be an object")
    for field, target in (("inventory_snapshot_id", "inventory_snapshot_id"), ("destination_id", "shortage_facility"),
                          ("medicine_id", "medicine_id"), ("quantity_unit", "quantity_unit")):
        if data[field] != baseline.get(target): raise ValidationError("Forecast and inventory context mismatch")
    maximum = integer(max_age_seconds, "max_age_seconds", 1)
    if maximum > 604800: raise ValidationError("Forecast maximum age cannot exceed seven days")
    age = (utc_now(now) - utc_timestamp(data["generated_at"], "generated_at")).total_seconds()
    if not 0 <= age <= maximum: raise ValidationError("Forecast is stale or future-dated")
    if not isinstance(data["periods"], list) or not 1 <= len(data["periods"]) <= 365:
        raise ValidationError("Forecast requires 1..365 daily demand entries")
    for period in data["periods"]:
        row = object_fields(period, required={"day", "demand"}, optional=set(), path="forecast period")
        integer(row["day"], "day")
        integer(row["demand"], "demand")
    result = run_timeline({"baseline": copy.deepcopy(baseline), "periods": copy.deepcopy(data["periods"]),
                           "policy": {} if policy is None else copy.deepcopy(policy)})
    result["forecast_provenance"] = {key: data[key] for key in ("forecast_id", "model_version", "generated_at", "inventory_snapshot_id")}
    return result
