"""Synchronous round coordinator; allowlisted IDs are not authentication."""

import copy
import logging

from federated.strategies.fedavg import MODEL_SCHEMA, fedavg, parameters, validate_update
from optimization.common.timestamps import utc_now, utc_timestamp
from optimization.common.validation import ValidationError, identifier, integer, nonnegative_number, object_fields

LOGGER = logging.getLogger(__name__)


class Coordinator:
    def __init__(self, nodes, *, min_clients=2, initial_model=None):
        if not isinstance(nodes, dict) or not 1 <= len(nodes) <= 100:
            raise ValidationError("nodes must map 1..100 node IDs to regions")
        minimum = integer(min_clients, "min_clients", 1)
        if minimum > len(nodes): raise ValidationError("min_clients exceeds registered nodes")
        self._minimum = minimum
        self._model = parameters({"weight": 0.0, "bias": 0.0} if initial_model is None else initial_model)
        self._version, self._round = 0, 1
        self._nodes = {identifier(node, "node_id"): {"region": identifier(region, "region"),
            "status": "registered", "last_seen": None, "round": None, "local_samples": None,
            "model_version": None, "training_duration_seconds": None, "metric_summary": None}
            for node, region in nodes.items()}

    def state(self):
        return copy.deepcopy({"model_schema": MODEL_SCHEMA, "min_clients": self._minimum, "model_version": self._version,
                              "next_round": self._round, "parameters": self._model, "nodes": self._nodes})

    @classmethod
    def from_state(cls, value):
        """Validate a complete snapshot before constructing a restored instance."""
        state = object_fields(value, required={"model_schema", "min_clients", "model_version", "next_round", "parameters", "nodes"},
                              optional=set(), path="checkpoint.state")
        if state["model_schema"] != MODEL_SCHEMA: raise ValidationError("Unsupported checkpoint model schema")
        version = integer(state["model_version"], "model_version")
        next_round = integer(state["next_round"], "next_round", 1)
        if version >= next_round: raise ValidationError("Checkpoint model version exceeds completed rounds")
        nodes = state["nodes"]
        if not isinstance(nodes, dict) or not 1 <= len(nodes) <= 100:
            raise ValidationError("Checkpoint requires 1..100 registered nodes")
        regions = {}
        observation_fields = {"last_seen", "round", "local_samples", "model_version", "training_duration_seconds", "metric_summary"}
        for node, raw in nodes.items():
            identifier(node, "node_id")
            metadata = object_fields(raw, required={"region", "status"} | observation_fields, optional=set(), path="node metadata")
            regions[node] = identifier(metadata["region"], "region")
            if metadata["status"] not in ("registered", "accepted", "rejected", "missing"):
                raise ValidationError("Unsupported node status")
            populated = [metadata[key] is not None for key in observation_fields]
            if any(populated) and not all(populated): raise ValidationError("Incomplete node observation metadata")
            if all(populated):
                utc_timestamp(metadata["last_seen"], "last_seen")
                observed_round = integer(metadata["round"], "node.round", 1)
                observed_version = integer(metadata["model_version"], "node.model_version")
                if observed_round >= next_round or observed_version > version or observed_version >= observed_round:
                    raise ValidationError("Node metadata is inconsistent with checkpoint version/round")
                samples = integer(metadata["local_samples"], "node.local_samples", 1)
                if samples > 10_000_000: raise ValidationError("Node sample count exceeds prototype limit")
                nonnegative_number(metadata["training_duration_seconds"], "training_duration_seconds")
                metrics = object_fields(metadata["metric_summary"], required={"local_training_mse"}, optional=set(), path="metric_summary")
                nonnegative_number(metrics["local_training_mse"], "local_training_mse")
            if metadata["status"] == "accepted" and (not all(populated) or metadata["round"] != next_round - 1):
                raise ValidationError("Accepted node lacks metadata for the latest round")
            if metadata["status"] == "registered" and (next_round != 1 or any(populated)):
                raise ValidationError("Registered status is only valid before the first round")
        restored = cls(regions, min_clients=state["min_clients"], initial_model=state["parameters"])
        restored._version, restored._round = version, next_round
        restored._nodes = copy.deepcopy(nodes)
        return restored

    def aggregate_round(self, updates, *, now=None):
        if not isinstance(updates, list) or len(updates) > 100:
            raise ValidationError("updates must contain at most 100 packets")
        # Duplicate identities abort the round before any state change. Never
        # let a duplicated packet double-count one node's sample weight.
        ids = [u.get("node_id") for u in updates if isinstance(u, dict) and isinstance(u.get("node_id"), str)]
        if len(ids) != len(set(ids)): raise ValidationError("Duplicate participant update in round")
        timestamp = utc_now(now).isoformat()
        accepted, rejected = [], []
        for raw in updates:
            node = raw.get("node_id") if isinstance(raw, dict) else None
            if not isinstance(node, str) or node not in self._nodes:
                rejected.append({"node_id": None, "reason": "unregistered_participant"})
                continue
            try:
                accepted.append(validate_update(raw, expected_round=self._round, expected_version=self._version))
            except ValidationError:
                rejected.append({"node_id": node, "reason": "invalid_update"})
        accepted.sort(key=lambda u: u["node_id"])
        completed = len(accepted) >= self._minimum
        # Compute before committing any model state. Updates are never retained.
        new_model = fedavg(accepted) if completed else self._model
        total = sum(u["local_samples"] for u in accepted)
        mean_loss = sum(u["metrics"]["local_training_mse"] * (u["local_samples"] / total)
                        for u in accepted) if total else None
        accepted_ids = {u["node_id"] for u in accepted}
        rejected_ids = {r["node_id"] for r in rejected}
        for node, metadata in self._nodes.items():
            metadata["status"] = "accepted" if node in accepted_ids else ("rejected" if node in rejected_ids else "missing")
        for update in accepted:
            metadata = self._nodes[update["node_id"]]
            metadata.update(last_seen=timestamp, round=self._round, local_samples=update["local_samples"],
                            model_version=update["model_version"], training_duration_seconds=update["training_duration_seconds"],
                            metric_summary=copy.deepcopy(update["metrics"]))
        previous_version = self._version
        if completed:
            self._model = new_model
            self._version += 1
        result = {"round": self._round, "status": "aggregated" if completed else "insufficient_participants",
                  "input_model_version": previous_version, "output_model_version": self._version,
                  "accepted_nodes": sorted(accepted_ids), "rejected_updates": rejected,
                  "missing_nodes": sorted(set(self._nodes) - accepted_ids - rejected_ids),
                  "total_samples": total, "weighted_local_training_mse": mean_loss,
                  "parameters": copy.deepcopy(self._model)}
        self._round += 1
        LOGGER.info("federation_round round=%d status=%s accepted=%d", result["round"], result["status"], len(accepted))
        return result
