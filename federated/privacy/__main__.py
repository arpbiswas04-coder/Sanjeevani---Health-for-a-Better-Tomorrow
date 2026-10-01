"""Synthetic privacy/utility demonstration; never accepts external training data."""
import argparse
import json
from pathlib import Path
import secrets
import sqlite3
from federated.clients.client import SyntheticClient
from federated.privacy.configuration import ConfiguredRelease, load, policy
from federated.clients.personalization import personalize
from federated.privacy.authenticated import AuthenticatedRound, signed
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from federated.privacy.secure_sum import MaskingClient
from optimization.common.validation import ValidationError


def run(rounds=3, *, ledger_path=None, initialize_ledger=False, learning_config=None):
    if type(rounds) is not int or not 1 <= rounds <= 10: raise ValidationError("Use 1..10 demo rounds")
    learning = load(learning_config or Path(__file__).parents[1] / "configs/learning.json")
    config = policy(learning["privacy"])
    clients = [SyntheticClient(node, [(x, 2*x+1) for x in values]) for node, values in (
        ("district-a", [-1, -.8, -.6, -.4]), ("district-b", [-.3, -.1, .1, .3, .5]), ("district-c", [.2, .4, .6, .8, 1, .9]))]
    from federated.privacy.ledger import PrivacyLedger
    ledger = PrivacyLedger(ledger_path, config, [c.node_id for c in clients], initialize=initialize_ledger) if ledger_path else None
    if initialize_ledger and ledger is None: raise ValidationError("Ledger path required")
    accountants = {client.node_id: ConfiguredRelease(learning["privacy"], ledger=ledger, node=client.node_id) for client in clients}
    private_model, reference = {"weight": 0.0, "bias": 0.0}, {"weight": 0.0, "bias": 0.0}
    identities = {c.node_id: Ed25519PrivateKey.generate() for c in clients}
    pinned = {n: k.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw) for n, k in identities.items()}
    history = []
    for round_id in range(1, rounds + 1):
        masking = {client.node_id: MaskingClient(client.node_id) for client in clients}
        public_keys = {node: client.public for node, client in masking.items()}
        nonce = secrets.token_hex(32)
        session = AuthenticatedRound(pinned, round_id, round_id - 1, nonce=nonce)
        announcements = [signed({**session.context, "node_id": n, "public_key": key.hex()}, identities[n]) for n, key in public_keys.items()]
        public_keys = session.establish(announcements)
        # Every participant independently verifies the same signed roster.
        for client in clients:
            peer_view = AuthenticatedRound(pinned, round_id, round_id - 1, nonce=nonce)
            if peer_view.establish(announcements) != public_keys:
                raise ValidationError("Peer roster mismatch")
        packets, controls = [], []
        for client in clients:
            update = client.train(private_model, round_id=round_id, model_version=round_id-1)
            delta = [update["parameters"][name] - private_model[name] for name in ("weight", "bias")]
            protected = accountants[client.node_id].release(delta)
            packet = masking[client.node_id].mask(protected, public_keys, nonce)
            packets.append(signed({**session.context, **packet}, identities[client.node_id]))
            # Nonprivate control uses PUBLIC SYNTHETIC data only; no such output on real data.
            controls.append(client.train(reference, round_id=round_id, model_version=round_id-1)["parameters"])
        average = session.aggregate(packets)
        private_model = {name: max(-1_000_000., min(1_000_000., private_model[name] + average[i])) for i, name in enumerate(("weight", "bias"))}
        reference = {name: sum(model[name] for model in controls)/len(controls) for name in ("weight", "bias")}
        def public_mse(model):
            return sum((model["weight"]*x + model["bias"] - (2*x+1))**2 for x in (-1, -.5, 0, .5, 1))/5
        history.append({"round": round_id, "private_public_grid_mse": public_mse(private_model),
                        "nonprivate_public_grid_mse": public_mse(reference),
                        "per_client_budget": max((a.mechanism.budget() for a in accountants.values()), key=lambda value: value["releases"]) if learning["privacy"]["enabled"] else None,
                        "client_budgets": {node: a.mechanism.budget() for node, a in accountants.items()} if learning["privacy"]["enabled"] else None})
    local_models = [personalize(c, private_model, learning["personalization"]) for c in clients]
    return {"privacy_enabled": learning["privacy"]["enabled"],
            "authenticated_masking": True, "personalized_nodes": sum(m["enabled"] for m in local_models),
            "mode": "synthetic_privacy_reference", "policy": config, "rounds": history,
            "model": private_model, "production_private_training": False,
            "accounting": "durable_sqlite" if ledger else "session_only",
            "limitations": ["In-process trusted harness can access client memory; only the aggregation API receives masked vectors.",
                            "Fixed public roster, equal client weighting; no sample counts or local losses released.",
                            "Analytical ideal-Gaussian client replacement bound; finite precision implementation is not audited.",
                            "Durable mode charges before release; copying/deleting/rolling back its database is not prevented. Session mode resets each run.",
                            "Signed ephemeral keys verified against pinned identities in a trusted harness; no distributed pin provisioning, dropout recovery or collusion defense.",
                            "Legacy HTTPS and FedAvg paths are unchanged and do not use this privacy prototype."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--learning-config", type=Path)
    parser.add_argument("--ledger", type=Path, help="Existing ledger under infra/federated/checkpoints")
    parser.add_argument("--initialize-ledger", action="store_true", help="Explicitly create a NEW synthetic-demo ledger once")
    args = parser.parse_args()
    try:
        if args.ledger and not args.ledger.resolve().is_relative_to(Path(__file__).resolve().parents[2] / "federated/checkpoints"):
            raise ValidationError("Ledger must remain in infra/federated/checkpoints")
        print(json.dumps(run(args.rounds, ledger_path=args.ledger, initialize_ledger=args.initialize_ledger, learning_config=args.learning_config), indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": "privacy_demo_failed", "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
