from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from app.schemas.platform import Input


class Adjustment(Input):
    facility_id: UUID
    batch_id: UUID
    quantity: int = Field(ge=-2_000_000_000, le=2_000_000_000, strict=True)
    kind: Literal['ADJUSTMENT','RETURN','DAMAGE','EXPIRED','RECALL'] = 'ADJUSTMENT'
    reference: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def sign(self):
        if self.quantity == 0 or (self.kind in ('DAMAGE','EXPIRED','RECALL') and self.quantity > 0) or (self.kind == 'RETURN' and self.quantity < 0):
            raise ValueError('Invalid quantity for transaction type')
        return self


class PolicyInput(Input):
    critical_days: float = Field(3, ge=0, le=3650)
    low_days: float = Field(7, ge=0, le=3650)
    lead_days: int = Field(7, ge=0, le=365)
    safety_stock: int = Field(0, ge=0, le=2_000_000_000)
    minimum_history_days: int = Field(7, ge=1, le=365)
    expiry_warning_days: int = Field(90, ge=1, le=3650)

    @model_validator(mode='after')
    def ordered(self):
        if self.low_days < self.critical_days:
            raise ValueError('Low threshold must be at least critical threshold')
        return self


class RecallInput(Input):
    batch_id: UUID
    reason: str = Field(min_length=1, max_length=1000)
    severity: Literal['low','high','critical']


class RecallResolution(Input):
    resolution: str = Field(min_length=1, max_length=1000)
