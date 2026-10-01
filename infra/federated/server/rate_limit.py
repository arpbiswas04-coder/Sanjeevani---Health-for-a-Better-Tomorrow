"""Bounded, per-identity token buckets for the sequential development server."""
import math
import time
from optimization.common.validation import ValidationError, integer


class IdentityLimiter:
    def __init__(self, identities, *, requests_per_minute=30, burst=10, clock=time.monotonic):
        self.rate = integer(requests_per_minute, "requests_per_minute", 1) / 60
        self.burst = integer(burst, "burst", 1)
        if requests_per_minute > 6000 or burst > 1000:
            raise ValidationError("Rate limit exceeds development bounds")
        self.clock = clock
        now = clock()
        self.buckets = {identity: (float(burst), now) for identity in identities}

    def retry_after(self, identity):
        """Consume one token; return zero if allowed, otherwise seconds to wait."""
        if identity not in self.buckets:
            return 60  # Unknown callers cannot grow limiter memory.
        tokens, previous = self.buckets[identity]
        now = max(previous, self.clock())
        tokens = min(self.burst, tokens + (now - previous) * self.rate)
        if tokens >= 1:
            self.buckets[identity] = (tokens - 1, now)
            return 0
        self.buckets[identity] = (tokens, now)
        return max(1, math.ceil((1 - tokens) / self.rate))
