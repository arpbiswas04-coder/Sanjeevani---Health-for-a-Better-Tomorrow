"""Bounded operational metrics; no keys, parameters, sample counts or losses."""
import time

MONITOR_URI = "urn:sanjeevani:monitor"


def is_monitor(certificate):
    identities = [value for kind, value in certificate.get("subjectAltName", ())
                  if kind == "URI" and value.startswith("urn:sanjeevani:")]
    return identities == [MONITOR_URI]


class Metrics:
    def __init__(self):
        self.started = time.time()
        self.accepted = 0
        self.rejected = 0
        self.rate_limited = 0
        self.rounds = 0
        self.insufficient = 0
        self.last_closed = 0
        self.last_checkpoint = 0
        self.close_seconds = 0

    def closed(self, result, duration):
        self.rounds += 1
        self.insufficient += int(result["status"] == "insufficient_participants")
        self.last_closed = time.time()
        self.close_seconds = duration

    def render(self, state):
        values = {
            "process_start_time_seconds": ("gauge", self.started),
            "updates_accepted_total": ("counter", self.accepted),
            "updates_rejected_total": ("counter", self.rejected),
            "requests_rate_limited_total": ("counter", self.rate_limited),
            "rounds_closed_total": ("counter", self.rounds),
            "rounds_insufficient_total": ("counter", self.insufficient),
            "last_round_closed_timestamp_seconds": ("gauge", self.last_closed),
            "last_checkpoint_timestamp_seconds": ("gauge", self.last_checkpoint),
            "last_round_close_duration_seconds": ("gauge", self.close_seconds),
            "model_version": ("gauge", state["model_version"]),
            "next_round": ("gauge", state["next_round"]),
        }
        for status in ("registered", "accepted", "rejected", "missing"):
            values[f"nodes_{status}"] = ("gauge", sum(n["status"] == status for n in state["nodes"].values()))
        lines = []
        for name, (kind, value) in values.items():
            full = "sanjeevani_federation_" + name
            lines.extend((f"# TYPE {full} {kind}", f"{full} {value}"))
        return ("\n".join(lines) + "\n").encode("ascii")
