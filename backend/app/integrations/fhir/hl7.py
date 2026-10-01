from typing import Protocol
from pydantic import BaseModel,Field


class HL7Envelope(BaseModel):
    """Routing metadata only; patient message contents are not persisted here."""
    sender:str=Field(min_length=1,max_length=100)
    message_type:str=Field(min_length=1,max_length=30)
    control_id:str=Field(min_length=1,max_length=100)


class HL7Adapter(Protocol):
    async def validate_and_map(self, raw_message: bytes) -> HL7Envelope:
        """Implement against the sender's agreed HL7 version/profile before enabling ingestion."""
        ...
