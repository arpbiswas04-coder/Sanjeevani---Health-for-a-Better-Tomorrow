"""Synthetic in-process simulation. This file plays the role of a test harness."""

import json
from importlib.resources import files

from federated.clients.client import SyntheticClient
from federated.server.coordinator import Coordinator
from federated.server.checkpoints import load_checkpoint, save_checkpoint
from optimization.common.validation import ValidationError, integer


def run_demo(rounds=None, *, resume_path=None, checkpoint_path=None):
    config = json.loads(files("federated").joinpath("configs/demo.json").read_text(encoding="utf-8"))
    count = config["rounds"] if rounds is None else integer(rounds, "rounds", 1)
    if count > 100: raise ValidationError("Demo rounds must be at most 100")
    # Samples are constructed and held by client instances, never placed in
    # the coordinator or update payload. Regions deliberately have different x.
    clients = [SyntheticClient(node, [(x, 2 * x + 1) for x in values]) for node, values in (
        ("district-a", [-1, -0.8, -0.6, -0.4]),
        ("district-b", [-0.3, -0.1, 0.1, 0.3, 0.5]),
        ("district-c", [0.2, 0.4, 0.6, 0.8, 1, 0.9]))]
    coordinator = load_checkpoint(resume_path) if resume_path is not None else Coordinator(config["nodes"], min_clients=config["min_clients"])
    restored = coordinator.state()
    if {node: value["region"] for node, value in restored["nodes"].items()} != config["nodes"] or restored["min_clients"] != config["min_clients"]:
        raise ValidationError("Checkpoint participant configuration does not match this demo")
    initial = {client.node_id: client.training_mse(coordinator.state()["parameters"]) for client in clients}
    history = []
    for _ in range(count):
        state = coordinator.state()
        updates = [client.train(state["parameters"], round_id=state["next_round"], model_version=state["model_version"],
                                local_epochs=config["local_epochs"], learning_rate=config["learning_rate"]) for client in clients]
        history.append(coordinator.aggregate_round(updates))
        if checkpoint_path is not None:
            save_checkpoint(coordinator, checkpoint_path)
    state = coordinator.state()
    return {"mode": "synthetic_in_process_demo", "rounds": history, "coordinator": state,
            "initial_local_training_mse": initial,
            "final_local_training_mse": {client.node_id: client.training_mse(state["parameters"]) for client in clients},
            "limitations": ["Synthetic two-parameter regression, not a health forecasting model.",
                            "All clients run in one process; no network or operating-system data isolation.",
                            "Node IDs are allowlisted, not authenticated; coordinator sees individual clear updates.",
                            "No differential privacy, secure aggregation or poisoning defense is implemented.",
                            "Metrics are training errors, not held-out evaluation or clinical validation."]}
