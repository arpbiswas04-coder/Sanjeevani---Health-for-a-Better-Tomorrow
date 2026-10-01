from typing import Protocol


class ResetDelivery(Protocol):
    async def deliver(self, user_id, token: str) -> None: ...


class MFAVerifier(Protocol):
    async def verify(self, user_id, proof: str) -> bool: ...


# Configure adapters in application composition. No token logging or fake delivery.
reset_delivery: ResetDelivery | None = None
mfa_verifier: MFAVerifier | None = None
