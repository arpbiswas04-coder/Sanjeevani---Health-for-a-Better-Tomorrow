"""Small gradient-descent client for deterministic synthetic demonstrations."""

import math
import time

from federated.strategies.fedavg import MODEL_SCHEMA, parameters
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number


class SyntheticClient:
    def __init__(self, node_id, samples):
        self.node_id = identifier(node_id, "node_id")
        if not isinstance(samples, list) or not samples:
            raise ValidationError("Synthetic client needs local (x, y) samples")
        self._samples = []
        for sample in samples:
            if not isinstance(sample, (list, tuple)) or len(sample) != 2:
                raise ValidationError("Each local sample must contain x and y")
            if any(type(v) not in (int, float) or abs(v) > 1000 or not math.isfinite(v) for v in sample):
                raise ValidationError("Synthetic sample is invalid or out of range")
            self._samples.append((float(sample[0]), float(sample[1])))

    def training_mse(self, model):
        model = parameters(model)
        return math.fsum((model["weight"] * x + model["bias"] - y) ** 2 for x, y in self._samples) / len(self._samples)

    def train(self, global_model, *, round_id, model_version, local_epochs=5, learning_rate=0.05):
        model = parameters(global_model)
        integer(round_id, "round_id", 1)
        integer(model_version, "model_version")
        epochs = integer(local_epochs, "local_epochs", 1)
        rate = nonnegative_number(learning_rate, "learning_rate")
        if epochs > 1000 or not 0 < rate <= 1:
            raise ValidationError("Prototype training requires 1..1000 epochs and learning rate in (0, 1]")
        started = time.perf_counter()
        for _ in range(epochs):
            errors = [model["weight"] * x + model["bias"] - y for x, y in self._samples]
            dw = 2 * math.fsum(error * sample[0] for error, sample in zip(errors, self._samples)) / len(errors)
            db = 2 * math.fsum(errors) / len(errors)
            model = parameters({"weight": model["weight"] - rate * dw, "bias": model["bias"] - rate * db})
        return {"node_id": self.node_id, "round": round_id, "model_version": model_version,
                "model_schema": MODEL_SCHEMA, "local_samples": len(self._samples),
                "training_duration_seconds": time.perf_counter() - started, "parameters": model,
                "metrics": {"local_training_mse": self.training_mse(model)}}
