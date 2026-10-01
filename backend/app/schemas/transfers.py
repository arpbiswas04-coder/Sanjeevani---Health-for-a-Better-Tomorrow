from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from app.schemas.platform import Input


class TransferLine(Input):
    batch_id: UUID
    quantity: int = Field(gt=0, le=2_000_000_000, strict=True)


class TransferCreate(Input):
    source_id: UUID
    destination_id: UUID
    reference: str = Field(min_length=1, max_length=200)
    items: list[TransferLine] = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def valid(self):
        if self.source_id == self.destination_id or len({i.batch_id for i in self.items}) != len(self.items):
            raise ValueError('Different facilities and distinct batches required')
        return self


class TransferAction(Input):
    action: Literal['approve','reject','dispatch','in_transit','receive','cancel']
    reason: str = Field(min_length=1, max_length=500)
