from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator, AwareDatetime
from app.schemas.platform import Input


class SupplierInput(Input):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    contact: str | None = Field(None, max_length=200)
    address: str | None = Field(None, max_length=500)
    lead_days: int = Field(7, ge=0, le=365)
    active: bool = True


class WarehouseInput(Input):
    facility_id: UUID
    capacity_units: int = Field(0, ge=0)
    cold_storage: bool = False


class OrderLine(Input):
    medicine_id: UUID
    quantity: int = Field(gt=0, le=2_000_000_000, strict=True)
    unit_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class OrderInput(Input):
    reference: str = Field(min_length=1, max_length=100)
    supplier_id: UUID
    facility_id: UUID
    items: list[OrderLine] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def distinct(self):
        if len({i.medicine_id for i in self.items}) != len(self.items):
            raise ValueError('Medicine lines must be unique')
        return self


class OrderAction(Input):
    action: Literal['submit','approve','order','cancel']
    note: str = Field(min_length=1, max_length=500)


class OrderReceipt(Input):
    item_id: UUID
    batch_number: str = Field(min_length=1, max_length=100)
    expires_on: date
    quantity: int = Field(gt=0, le=2_000_000_000, strict=True)
    idempotency_key: str = Field(min_length=1, max_length=100)


class ShipmentInput(Input):
    reference: str = Field(min_length=1, max_length=100)
    order_id: UUID | None = None
    transfer_id: UUID | None = None
    origin: str = Field(min_length=1, max_length=200)
    expected_at: AwareDatetime
    vehicle: str | None = Field(None, max_length=100)
    carrier: str | None = Field(None, max_length=100)

    @model_validator(mode='after')
    def one_source(self):
        if (self.order_id is None) == (self.transfer_id is None):
            raise ValueError('Supply exactly one order or transfer')
        return self


class ShipmentAction(Input):
    status: Literal['dispatched','in_transit','arrived','cancelled']
    note: str = Field(min_length=1, max_length=500)

class WarehouseUpdate(Input):
    capacity_units: int = Field(0, ge=0)
    cold_storage: bool = False
    active: bool = True
