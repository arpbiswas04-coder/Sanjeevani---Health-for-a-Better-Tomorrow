from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


class FacilityCreate(Input):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)


class MedicineCreate(FacilityCreate):
    unit: str = Field(min_length=1, max_length=50)


class Receive(Input):
    idempotency_key: str | None = Field(None, min_length=1, max_length=100)
    facility_id: UUID
    medicine_id: UUID
    batch_number: str = Field(min_length=1, max_length=100)
    expires_on: date
    quantity: int = Field(gt=0, le=2_000_000_000, strict=True)
    reference: str = Field(min_length=1, max_length=200)


class Issue(Input):
    idempotency_key: str | None = Field(None, min_length=1, max_length=100)
    facility_id: UUID
    medicine_id: UUID
    quantity: int = Field(gt=0, le=2_000_000_000, strict=True)
    reference: str = Field(min_length=1, max_length=200)
