"""Local subprocess harness for Flower-compatible PyTorch clients.

This is not Flower's network runtime. The existing validated coordinator owns
rounds/FedAvg/checkpoints; Flower's NumPyClient interface owns client callbacks.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from federated.server.checkpoints import load_checkpoint, save_checkpoint
from federated.server.coordinator import Coordinator
from federated.registry import load as load_registry
from optimization.common.validation import ValidationError, integer, nonnegative_number

NODES = {"district-a": "region-a", "district-b": "region-b", "district-c": "region-c"}


def _regional_call(node, state, action, timeout):
    payload = {"node_id": node, "action": action, "parameters": state["parameters"],
               "round": state["next_round"], "model_version": state["model_version"]}
    environment = {**os.environ, "FLWR_TELEMETRY_ENABLED": "0", "OMP_NUM_THREADS": "1"}
    try:
        process = subprocess.run([sys.executable, "-m", "federated.clients.regional_worker"],
            input=json.dumps(payload), capture_output=True, text=True, timeout=timeout,
            cwd=Path(__file__).resolve().parents[1], env=environment)
        if process.returncode != 0 or len(process.stdout) > 65536:
            return {"node_id": node, "error": "worker_failed"}
        reply = json.loads(process.stdout)
        if not isinstance(reply, dict) or reply.get("node_id") != node:
            return {"node_id": node, "error": "invalid_worker_reply"}
        if action == "fit" and (not isinstance(reply.get("update"), dict) or reply["update"].get("node_id") != node):
            return {"node_id": node, "error": "invalid_worker_identity"}
        integer(reply.get("process_id"), "process_id", 1)
        integer(reply.get("evaluation_samples"), "evaluation_samples", 1)
        nonnegative_number(reply.get("heldout_mse"), "heldout_mse")
        version = integer(reply.get("evaluation_model_version"), "evaluation_model_version")
        if version != state["model_version"]:
            return {"node_id": node, "error": "evaluation_version_mismatch"}
        return reply
    except subprocess.TimeoutExpired:
        return {"node_id": node, "error": "worker_timeout"}
    except (ValueError, OSError):
        return {"node_id": node, "error": "worker_failed"}


def run_regional(rounds=3, *, timeout_seconds=60, checkpoint_path=None, resume_path=None):
    count = integer(rounds, "rounds", 1)
    timeout = nonnegative_number(timeout_seconds, "timeout_seconds")
    if count > 100 or not 1 <= timeout <= 300: raise ValidationError("Unsupported rounds or timeout")
    if any(importlib.util.find_spec(name) is None for name in ("torch", "flwr")):
        raise RuntimeError("Run with the optional Flower/PyTorch environment")
    registry = load_registry(Path(__file__).parent / "configs/regions.json")
    if {node: meta["region"] for node, meta in registry.items()} != NODES:
        raise ValidationError("Registry does not match the registered demo participants")
    coordinator = load_checkpoint(resume_path) if resume_path else Coordinator(NODES)
    state = coordinator.state()
    if {n: m["region"] for n, m in state["nodes"].items()} != NODES or state["min_clients"] != 2:
        raise ValidationError("Regional checkpoint participant configuration mismatch")
    history, failures, evaluations = [], [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for _ in range(count):
            state = coordinator.state()
            replies = list(pool.map(lambda node: _regional_call(node, state, "fit", timeout), NODES))
            valid = [reply for reply in replies if "error" not in reply]
            failures.extend({**reply, "round": state["next_round"]} for reply in replies if "error" in reply)
            evaluations.append({"model_version": state["model_version"],
                                "regions": [{key: reply[key] for key in ("node_id", "heldout_mse", "evaluation_samples", "process_id")}
                                            for reply in valid]})
            history.append(coordinator.aggregate_round([reply["update"] for reply in valid]))
            if checkpoint_path: save_checkpoint(coordinator, checkpoint_path)
            if history[-1]["status"] != "aggregated": break
        state = coordinator.state()
        final = list(pool.map(lambda node: _regional_call(node, state, "evaluate", timeout), NODES))
    return {"public_node_registry": registry, "mode": "local_subprocess_flower_pytorch_adapter", "rounds": history,
            "status": "completed" if len(history) == count and all(r["status"] == "aggregated" for r in history) else "insufficient_participants",
            "coordinator": state, "worker_failures": failures, "evaluations_before_rounds": evaluations,
            "final_evaluation": {"model_version": state["model_version"],
                                 "complete": all("error" not in reply for reply in final), "regions": final},
            "limitations": ["Synthetic model and held-out data; not a healthcare model.",
                            "Local subprocess harness, not a Flower SuperLink/SuperNode deployment.",
                            "Same operating-system user; no authenticated network, sandboxed data isolation, secure aggregation or differential privacy."]}


def main():
    parser = argparse.ArgumentParser(description="Regional Flower/PyTorch adapter demo")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[1]
        for path in (args.checkpoint, args.resume):
            if path is not None and not path.resolve().is_relative_to(root): raise ValidationError("Paths must stay inside infra")
        result = run_regional(args.rounds, timeout_seconds=args.timeout, checkpoint_path=args.checkpoint, resume_path=args.resume)
    except (ValidationError, RuntimeError, OSError) as exc:
        print(json.dumps({"error": "regional_run_failed", "message": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["status"] == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
