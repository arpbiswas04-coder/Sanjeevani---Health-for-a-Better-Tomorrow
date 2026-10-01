from datetime import date,datetime,timezone
from typing import Literal
from uuid import UUID
from pydantic import Field,AwareDatetime,model_validator
from app.schemas.platform import Input


class TemperatureInput(Input):
    facility_id:UUID
    shipment_id:UUID|None=None
    observed_at:AwareDatetime
    temperature:float=Field(ge=-100,le=150)
    minimum:float=Field(ge=-100,le=150)
    maximum:float=Field(ge=-100,le=150)
    source:str=Field(min_length=1,max_length=100)
    external_id:str=Field(min_length=1,max_length=100)

    @model_validator(mode='after')
    def valid(self):
        if self.minimum>=self.maximum or self.observed_at>datetime.now(timezone.utc):
            raise ValueError('Invalid limits or future observation')
        return self


class BedInput(Input):
    facility_id:UUID
    bed_type:str=Field(min_length=1,max_length=50)
    capacity:int=Field(ge=0,le=100000,strict=True)
    occupied:int=Field(ge=0,le=100000,strict=True)

    @model_validator(mode='after')
    def valid(self):
        if self.occupied>self.capacity:
            raise ValueError('Occupancy exceeds capacity')
        return self


class StaffRoleInput(Input):
    name:str=Field(min_length=1,max_length=100)


class StaffInput(Input):
    facility_id:UUID
    staff_role_id:UUID
    code:str=Field(min_length=1,max_length=50)
    display_name:str=Field(min_length=1,max_length=200)
    active:bool=True


class ShiftInput(Input):
    staff_id:UUID
    starts_at:AwareDatetime
    ends_at:AwareDatetime

    @model_validator(mode='after')
    def valid(self):
        if not 0<(self.ends_at-self.starts_at).total_seconds()<=86400:
            raise ValueError('Shift length must be between zero and 24 hours')
        return self


class AttendanceInput(Input):
    staff_id:UUID
    day:date
    status:Literal['present','absent','leave']


class AggregateInput(Input):
    facility_id:UUID
    day:date
    category:str=Field(min_length=1,max_length=100)
    count:int=Field(ge=0,le=2_000_000_000,strict=True)
    expected_version:int=Field(0,ge=0)
    source_device:str|None=Field(None,max_length=100)
