from typing import Protocol
from app.schemas.integrations import PopulationInput


class PopulationProvider(Protocol):
    async def fetch(self, geographic_code: str) -> PopulationInput:
        """Return validated official-source data and provenance; never synthesize counts."""
        ...
