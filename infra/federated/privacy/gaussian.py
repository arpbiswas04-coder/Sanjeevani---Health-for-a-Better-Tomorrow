"""Client-level clipped Gaussian releases with conservative zCDP composition.

This reference uses an ideal-Gaussian analysis with finite precision sampling.
It is not production-audited. Optional PrivacyLedger provides durable demo counters.
"""
import math
import random
from optimization.common.validation import ValidationError, nonnegative_number, object_fields


def vector(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValidationError("Expected two model coordinates")
    if any(type(x) not in (int, float) for x in value):
        raise ValidationError("Model coordinates must be numbers")
    try:
        values = [float(x) for x in value]
    except OverflowError as exc:
        raise ValidationError("Coordinate exceeds bounds") from exc
    if any(not math.isfinite(x) or abs(x) > 1_000_000 for x in values):
        raise ValidationError("Nonfinite or out-of-bounds coordinate")
    return values


class GaussianRelease:
    def __init__(self, config, *, ledger=None, node=None):
        policy = object_fields(config, required={"clipping_norm", "noise_multiplier", "delta", "max_epsilon"}, optional=set(), path="privacy")
        self.clip = nonnegative_number(policy["clipping_norm"], "clipping_norm")
        self.sigma = nonnegative_number(policy["noise_multiplier"], "noise_multiplier")
        self.delta = nonnegative_number(policy["delta"], "delta")
        self.maximum = nonnegative_number(policy["max_epsilon"], "max_epsilon")
        if not 1e-6 <= self.clip <= 1000 or not .01 <= self.sigma <= 100 or not 1e-12 <= self.delta < 1 or not 0 < self.maximum <= 1000:
            raise ValidationError("Unsupported privacy configuration")
        self.ledger, self.node = ledger, node
        self.releases = ledger.snapshot()[node] if ledger is not None else 0
        self._random = random.SystemRandom()

    def budget(self, releases=None):
        steps = self.releases if releases is None else releases
        rho = steps / (2 * self.sigma ** 2)
        return {"releases": steps, "rho": rho, "epsilon": rho + 2 * math.sqrt(rho * math.log(1 / self.delta)), "delta": self.delta}

    def release(self, update_delta):
        values = vector(update_delta)
        norm = math.hypot(*values)
        factor = min(1.0, self.clip / norm) if norm else 1.0
        next_budget = self.budget(self.releases + 1)
        if next_budget["epsilon"] > self.maximum:
            raise ValidationError("Privacy budget exhausted before release")
        # Replace-one-client adjacency: clipped vectors differ by at most 2C.
        deviation = 2 * self.clip * self.sigma
        # Charge before sampling; a failed/aborted round does not refund releases.
        self.releases = (self.ledger.reserve(self.node, self.budget, self.maximum)
                         if self.ledger is not None else self.releases + 1)
        return [max(-1_000_000.0, min(1_000_000.0, x * factor + self._random.normalvariate(0, deviation))) for x in values]
