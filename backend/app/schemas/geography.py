from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from app.schemas.platform import Input


class GeographyCreate(Input):
    name: str = Field(min_length=1, max_length=150)
    code: str = Field(min_length=1, max_length=8)
    parent_id: UUID | None = None


class FacilityUpdate(Input):
    name: str | None = Field(None, min_length=1, max_length=200)
    facility_type: Literal['phc', 'hospital', 'clinic', 'warehouse', 'other'] | None = None
    address: str | None = Field(None, max_length=500)
    block_id: UUID | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    contact: str | None = Field(None, max_length=200)
    active: bool | None = None

    @model_validator(mode='after')
    def paired_coordinates(self):
        if ('latitude' in self.model_fields_set) != ('longitude' in self.model_fields_set):
            raise ValueError('Set latitude and longitude together')
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError('Both coordinates are required')
        return self
