from typing import Literal
from uuid import UUID
from pydantic import Field
from app.schemas.platform import Input


class ReportRequest(Input):
    facility_id:UUID
    kind:Literal['stock','expiry','transfers','procurement','staff','beds','emergency']
    format:Literal['csv','xlsx','pdf']='csv'


class ScheduleRequest(ReportRequest):
    interval_minutes:int=Field(ge=30,le=525600)
