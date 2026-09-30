"""Synthetic privacy/utility demonstration; never accepts external training data."""
import argparse
import json
from pathlib import Path
import secrets
import sqlite3
from federated.clients.client import SyntheticClient
from federated.privacy.gaussian import GaussianRelease
from federated.privacy.secure_sum import MaskingClient, aggregate
from optimization.common.validation import ValidationError


def run(rounds=3, *, ledger_path=None, initialize_ledger=False):
    if type(rounds) is not int or not 1 <= rounds <= 10: raise ValidationError("Use 1..10 demo rounds")
    config = json.loads(Path(__file__).with_name("policy.json").read_text())
    clients = [SyntheticClient(node, [(x, 2*x+1) for x in values]) for node, values in (
        ("district-a", [-1, -.8, -.6, -.4]), ("district-b", [-.3, -.1, .1, .3, .5]), ("district-c", [.2, .4, .6, .8, 1, .9]))]
    from federated.privacy.ledger import PrivacyLedger
    ledger = PrivacyLedger(ledger_path, config, [c.node_id for c in clients], initialize=initialize_ledger) if ledger_path else None
    if initialize_ledger and ledger is None: raise ValidationError("Ledger path required")
    accountants = {client.node_id: GaussianRelease(config, ledger=ledger, node=client.node_id) for client in clients}
    private_model, reference = {"weight": 0.0, "bias": 0.0}, {"weight": 0.0, "bias": 0.0}
    history = []
    for round_id in range(1, rounds + 1):
        masking = {client.node_id: MaskingClient(client.node_id) for client in clients}
        public_keys = {node: client.public for node, client in masking.items()}
        nonce = secrets.token_hex(32)
        packets, controls = [], []
        for client in clients:
            update = client.train(private_model, round_id=round_id, model_version=round_id-1)
            delta = [update["parameters"][name] - private_model[name] for name in ("weight", "bias")]
            protected = accountants[client.node_id].release(delta)
            packets.append(masking[client.node_id].mask(protected, public_keys, nonce))
            # Nonprivate control uses PUBLIC SYNTHETIC data only; no such output on real data.
            controls.append(client.train(reference, round_id=round_id, model_version=round_id-1)["parameters"])
        average = aggregate(packets, public_keys, nonce)
        private_model = {name: max(-1_000_000., min(1_000_000., private_model[name] + average[i])) for i, name in enumerate(("weight", "bias"))}
        reference = {name: sum(model[name] for model in controls)/len(controls) for name in ("weight", "bias")}
        def public_mse(model):
            return sum((model["weight"]*x + model["bias"] - (2*x+1))**2 for x in (-1, -.5, 0, .5, 1))/5
        history.append({"round": round_id, "private_public_grid_mse": public_mse(private_model),
                        "nonprivate_public_grid_mse": public_mse(reference),
                        "per_client_budget": max((a.budget() for a in accountants.values()), key=lambda value: value["releases"]),
                        "client_budgets": {node: a.budget() for node, a in accountants.items()}})
    return {"mode": "synthetic_privacy_reference", "policy": config, "rounds": history,
            "model": private_model, "production_private_training": False,
            "accounting": "durable_sqlite" if ledger else "session_only",
            "limitations": ["In-process trusted harness can access client memory; only the aggregation API receives masked vectors.",
                            "Fixed public roster, equal client weighting; no sample counts or local losses released.",
                            "Analytical ideal-Gaussian client replacement bound; finite precision implementation is not audited.",
                            "Durable mode charges before release; copying/deleting/rolling back its database is not prevented. Session mode resets each run.",
                            "No authenticated peer-key exchange, dropout recovery, collusion or malicious-client defense.",
                            "Legacy HTTPS and FedAvg paths are unchanged and do not use this privacy prototype."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--ledger", type=Path, help="Existing ledger under infra/federated/checkpoints")
    parser.add_argument("--initialize-ledger", action="store_true", help="Explicitly create a NEW synthetic-demo ledger once")
    args = parser.parse_args()
    try:
        if args.ledger and not args.ledger.resolve().is_relative_to(Path(__file__).resolve().parents[2] / "federated/checkpoints"):
            raise ValidationError("Ledger must remain in infra/federated/checkpoints")
        print(json.dumps(run(args.rounds, ledger_path=args.ledger, initialize_ledger=args.initialize_ledger), indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": "privacy_demo_failed", "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
