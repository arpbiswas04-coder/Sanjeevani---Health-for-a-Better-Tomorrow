"""Optional Flower NumPyClient adapter backed by a CPU PyTorch model."""

import time

from federated.strategies.fedavg import MODEL_SCHEMA, parameters
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields


def create_client(node_id, training_samples, evaluation_samples):
    """Create a Flower-compatible client with local training/held-out samples.

    The two-array schema is [weight (1, 1), bias (1,)], float64. This reference
    schema must be replaced/versioned with Member 3's actual forecasting model.
    """
    try:
        import numpy as np
        import torch
        from flwr.client import NumPyClient
    except ImportError as exc:
        raise RuntimeError("Install the optional Flower/PyTorch federation dependencies") from exc
    node = identifier(node_id, "node_id")

    def local_tensors(samples):
        if not isinstance(samples, list) or not 1 <= len(samples) <= 100000:
            raise ValidationError("Local dataset must contain 1..100000 (x,y) samples")
        for sample in samples:
            if not isinstance(sample, (tuple, list)) or len(sample) != 2 or any(type(v) not in (int, float) for v in sample):
                raise ValidationError("Local samples must be numeric (x,y) pairs")
        values = np.asarray(samples, dtype=np.float64)
        if not np.isfinite(values).all() or np.abs(values).max() > 1000:
            raise ValidationError("Local samples exceed the reference model bounds")
        return torch.tensor(values[:, :1].copy()), torch.tensor(values[:, 1:].copy())

    train_x, train_y = local_tensors(training_samples)
    eval_x, eval_y = local_tensors(evaluation_samples)

    class RegionalClient(NumPyClient):
        def __init__(self):
            self.model = torch.nn.Linear(1, 1, dtype=torch.float64)
            with torch.no_grad():
                self.model.weight.zero_()
                self.model.bias.zero_()

        def _load(self, arrays):
            if not isinstance(arrays, list) or len(arrays) != 2:
                raise ValidationError("Expected exactly two parameter arrays")
            for array, shape in zip(arrays, ((1, 1), (1,))):
                if not isinstance(array, np.ndarray) or array.shape != shape or array.dtype != np.float64:
                    raise ValidationError("Parameter tensor shape/dtype does not match model schema")
                if not np.isfinite(array).all() or np.abs(array).max() > 1_000_000:
                    raise ValidationError("Parameter tensor is non-finite or out of bounds")
            with torch.no_grad():
                self.model.weight.copy_(torch.from_numpy(arrays[0].copy()))
                self.model.bias.copy_(torch.from_numpy(arrays[1].copy()))

        def get_parameters(self, config):
            return [self.model.weight.detach().cpu().numpy().copy(), self.model.bias.detach().cpu().numpy().copy()]

        def get_properties(self, config):
            return {"node_id": node, "model_schema": MODEL_SCHEMA}

        def fit(self, arrays, config):
            settings = object_fields(config, required={"round", "model_version", "model_schema", "local_epochs", "learning_rate"},
                                     optional=set(), path="fit.config")
            if settings["model_schema"] != MODEL_SCHEMA: raise ValidationError("Incompatible model schema")
            round_id = integer(settings["round"], "round", 1)
            version = integer(settings["model_version"], "model_version")
            epochs = integer(settings["local_epochs"], "local_epochs", 1)
            rate = nonnegative_number(settings["learning_rate"], "learning_rate")
            if epochs > 1000 or not 0 < rate <= 1: raise ValidationError("Invalid training configuration")
            self._load(arrays)
            started = time.perf_counter()
            self.model.train()
            optimizer = torch.optim.SGD(self.model.parameters(), lr=rate)
            for _ in range(epochs):
                optimizer.zero_grad()
                loss = torch.nn.functional.mse_loss(self.model(train_x), train_y)
                if not torch.isfinite(loss): raise ValidationError("Non-finite training loss")
                loss.backward()
                optimizer.step()
            trained = self.get_parameters({})
            self._load(trained)  # Validate output bounds as well as input tensors.
            self.model.eval()
            with torch.no_grad():
                mse = float(torch.nn.functional.mse_loss(self.model(train_x), train_y).item())
            return trained, len(train_x), {"node_id": node, "round": round_id, "model_version": version,
                "model_schema": MODEL_SCHEMA, "training_duration_seconds": time.perf_counter() - started,
                "local_training_mse": mse}

        def evaluate(self, arrays, config):
            if config.get("model_schema") != MODEL_SCHEMA: raise ValidationError("Incompatible evaluation model schema")
            self._load(arrays)
            self.model.eval()
            with torch.no_grad():
                mse = float(torch.nn.functional.mse_loss(self.model(eval_x), eval_y).item())
            return mse, len(eval_x), {"node_id": node, "heldout_mse": mse}

    return RegionalClient()


def to_arrays(model):
    import numpy as np
    model = parameters(model)
    return [np.array([[model["weight"]]], dtype=np.float64), np.array([model["bias"]], dtype=np.float64)]


def synthetic_region_client(node_id):
    regions = {"district-a": ([-1, -.8, -.6, -.4], [-.9, -.7]),
               "district-b": ([-.3, -.1, .1, .3, .5], [-.2, .2]),
               "district-c": ([.2, .4, .6, .8, 1, .9], [.35, .75])}
    if node_id not in regions: raise ValidationError("Unknown synthetic regional node")
    training, heldout = regions[node_id]
    return create_client(node_id, [(x, 2*x + 1) for x in training], [(x, 2*x + 1) for x in heldout])
