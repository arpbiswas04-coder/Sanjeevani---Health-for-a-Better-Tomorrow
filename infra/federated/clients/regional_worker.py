"""One bounded stdin/stdout exchange. Samples are constructed only in this process."""

import json
import os
import sys

from federated.clients.flower_torch import synthetic_region_client, to_arrays
from federated.strategies.fedavg import MODEL_SCHEMA, parameters
from optimization.common.validation import ValidationError, identifier, integer, object_fields


def execute(request):
    data = object_fields(request, required={"node_id", "action", "parameters", "round", "model_version"}, optional=set(), path="worker request")
    node = identifier(data["node_id"], "node_id")
    round_id = integer(data["round"], "round", 1)
    version = integer(data["model_version"], "model_version")
    if data["action"] not in ("fit", "evaluate"): raise ValidationError("Unsupported regional action")
    model = parameters(data["parameters"])
    import torch
    torch.set_num_threads(1)
    client = synthetic_region_client(node)
    arrays = to_arrays(model)
    initial_mse, eval_count, _ = client.evaluate(arrays, {"model_schema": MODEL_SCHEMA})
    response = {"node_id": node, "process_id": os.getpid(), "evaluation_model_version": version,
                "heldout_mse": initial_mse, "evaluation_samples": eval_count}
    if data["action"] == "fit":
        arrays, count, metrics = client.fit(arrays, {"round": round_id, "model_version": version,
            "model_schema": MODEL_SCHEMA, "local_epochs": 10, "learning_rate": 0.05})
        response["update"] = {"node_id": node, "round": round_id, "model_version": version,
            "model_schema": MODEL_SCHEMA, "local_samples": count,
            "training_duration_seconds": metrics["training_duration_seconds"],
            "parameters": {"weight": float(arrays[0][0, 0]), "bias": float(arrays[1][0])},
            "metrics": {"local_training_mse": metrics["local_training_mse"]}}
    return response


def main():
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384: raise ValidationError("Worker request exceeds size limit")
        result = execute(json.loads(raw))
        print(json.dumps(result, allow_nan=False))
        return 0
    except (ValueError, ImportError, RuntimeError, OSError):
        print(json.dumps({"error": "regional_worker_failed"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
