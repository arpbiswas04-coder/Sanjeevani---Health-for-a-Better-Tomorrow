from datetime import date
from uuid import UUID
from typing import Literal
from pydantic import Field,model_validator,AwareDatetime,HttpUrl
from app.schemas.platform import Input
from app.schemas.transfers import TransferLine


class RecommendationInput(Input):
    source_id:UUID
    destination_id:UUID
    model_version:str=Field(min_length=1,max_length=100)
    items:list[TransferLine]=Field(min_length=1,max_length=100)
    predicted_demand:int|None=Field(None,ge=0,le=2_000_000_000)
    transport_note:str|None=Field(None,max_length=500)

    @model_validator(mode='after')
    def valid(self):
        if self.source_id==self.destination_id or len({i.batch_id for i in self.items})!=len(self.items):
            raise ValueError('Invalid redistribution recommendation')
        return self


class RecommendationAction(Input):
    action:Literal['approve','reject','apply']


class PopulationInput(Input):
    district_id:UUID
    population:int=Field(ge=0,le=2_000_000_000,strict=True)
    source:str=Field(min_length=1,max_length=200)
    source_url:HttpUrl
    as_of:date
    retrieved_at:AwareDatetime


class BarcodeInput(Input):
    code:str=Field(pattern=r'^[A-Za-z0-9._:/-]{1,128}$')
    medicine_id:UUID|None=None
    batch_id:UUID|None=None

    @model_validator(mode='after')
    def valid(self):
        if (self.medicine_id is None)==(self.batch_id is None):
            raise ValueError('Barcode must identify one medicine or batch')
        return self


class BackupInput(Input):
    artifact_key:str=Field(pattern=r'^[A-Za-z0-9_-][A-Za-z0-9._-]{0,199}$')
    status:Literal['completed','failed']
    checksum:str|None=Field(None,pattern=r'^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)
    started_at:AwareDatetime
    completed_at:AwareDatetime|None=None
    verified_at:AwareDatetime|None=None

    @model_validator(mode='after')
    def valid(self):
        if self.status=='completed' and (not self.checksum or not self.completed_at or self.size_bytes==0):
            raise ValueError('Completed backups require checksum, completion time and size')
        if self.completed_at and self.completed_at<self.started_at:
            raise ValueError('Completion precedes start')
        if self.verified_at and (not self.completed_at or self.verified_at<self.completed_at):
            raise ValueError('Verification precedes completion')
        return self
