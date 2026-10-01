from app.core.time import utc_today
from datetime import date,datetime,timezone
from typing import Literal
from uuid import UUID
from pydantic import Field,model_validator
from app.schemas.platform import Input


class EquipmentInput(Input):
    facility_id:UUID
    code:str=Field(min_length=1,max_length=80)
    equipment_type:str=Field(min_length=1,max_length=100)
    status:Literal['available','in_use','maintenance','retired']='available'
    next_maintenance:date|None=None
    notes:str|None=Field(None,max_length=1000)


class MaintenanceInput(Input):
    performed_on:date
    next_due:date
    notes:str=Field(min_length=1,max_length=1000)

    @model_validator(mode='after')
    def valid(self):
        if self.next_due<=self.performed_on or self.performed_on>utc_today():
            raise ValueError('Invalid maintenance dates')
        return self


class AmbulanceInput(Input):
    facility_id:UUID
    vehicle_id:str=Field(min_length=1,max_length=80)
    status:Literal['available','assigned','in_transit','maintenance','retired']='available'
    operational:bool=True
    latitude:float|None=Field(None,ge=-90,le=90)
    longitude:float|None=Field(None,ge=-180,le=180)

    @model_validator(mode='after')
    def valid(self):
        if (self.latitude is None)!=(self.longitude is None):
            raise ValueError('Coordinates must be paired')
        if not self.operational and self.status=='available':
            raise ValueError('Non-operational ambulance cannot be available')
        return self
