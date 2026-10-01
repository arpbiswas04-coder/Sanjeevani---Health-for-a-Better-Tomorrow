"""Deliberately limited FHIR R4 Location export; not a FHIR server."""
from typing import Literal
from pydantic import BaseModel,Field


class Position(BaseModel):
    longitude:float=Field(ge=-180,le=180)
    latitude:float=Field(ge=-90,le=90)


class Location(BaseModel):
    resourceType:Literal['Location']='Location'
    id:str
    status:Literal['active','inactive']
    name:str
    position:Position|None=None


def facility_location(facility):
    position=None
    if facility.latitude is not None and facility.longitude is not None:
        position=Position(latitude=facility.latitude,longitude=facility.longitude)
    return Location(id=str(facility.id),status='active' if facility.active else 'inactive',name=facility.name,position=position).model_dump(exclude_none=True)
