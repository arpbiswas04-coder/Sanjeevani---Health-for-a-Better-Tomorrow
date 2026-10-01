"""Validated sample-weighted averaging for a two-parameter reference model."""

import math

from optimization.common.validation import ValidationError, nonnegative_number, object_fields, integer, identifier

MODEL_SCHEMA = "synthetic-linear-v1"


def parameters(value):
    row = object_fields(value, required={"weight", "bias"}, optional=set(), path="parameters")
    result = {}
    for name, number in row.items():
        if type(number) not in (int, float): raise ValidationError("Model parameters must be finite numbers")
        try:
            numeric = float(number)
        except OverflowError as exc:
            raise ValidationError("Model parameter magnitude exceeds prototype limit") from exc
        if not math.isfinite(numeric) or abs(numeric) > 1_000_000:
            raise ValidationError("Model parameter is non-finite or exceeds prototype limit")
        result[name] = numeric
    return result


def validate_update(value, *, expected_round, expected_version):
    update = object_fields(value, required={"node_id", "round", "model_version", "model_schema",
        "local_samples", "training_duration_seconds", "parameters", "metrics"}, optional=set(), path="update")
    node = identifier(update["node_id"], "update.node_id")
    round_id = integer(update["round"], "update.round", 1)
    version = integer(update["model_version"], "update.model_version")
    if round_id != expected_round or version != expected_version:
        raise ValidationError("Stale or mismatched round/model version")
    if update["model_schema"] != MODEL_SCHEMA: raise ValidationError("Incompatible model schema")
    samples = integer(update["local_samples"], "update.local_samples", 1)
    if samples > 10_000_000: raise ValidationError("Sample count exceeds prototype limit")
    duration = nonnegative_number(update["training_duration_seconds"], "update.training_duration_seconds")
    metrics = object_fields(update["metrics"], required={"local_training_mse"}, optional=set(), path="metrics")
    mse = nonnegative_number(metrics["local_training_mse"], "metrics.local_training_mse")
    return {"node_id": node, "round": round_id, "model_version": version, "model_schema": MODEL_SCHEMA,
            "local_samples": samples, "training_duration_seconds": duration,
            "parameters": parameters(update["parameters"]), "metrics": {"local_training_mse": mse}}


def fedavg(updates):
    """Aggregate already validated updates. Inputs are not modified."""
    if not updates: raise ValidationError("FedAvg requires at least one valid update")
    total = sum(update["local_samples"] for update in updates)
    return {name: math.fsum(update["parameters"][name] * (update["local_samples"] / total)
                            for update in updates) for name in ("weight", "bias")}
