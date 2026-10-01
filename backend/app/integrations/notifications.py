from typing import Protocol


class NotificationProvider(Protocol):
    async def send(self, *, recipient_id, template: str, data: dict, idempotency_key: str) -> None: ...


class DevelopmentProvider:
    """Explicit test adapter; never registered in production by default."""
    def __init__(self):
        self.deliveries = {}

    async def send(self, *, recipient_id, template, data, idempotency_key):
        self.deliveries.setdefault(idempotency_key, {'recipient_id': recipient_id, 'template': template, 'data': data})


providers: dict[str, NotificationProvider] = {}
