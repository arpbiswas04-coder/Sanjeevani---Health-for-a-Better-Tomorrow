from typing import Literal
from pydantic import Field
from app.schemas.platform import Input
from app.schemas.operations import AggregateInput


class SyncItem(Input):
    kind:Literal['footfall','disease-counts']
    payload:AggregateInput


class SyncPush(Input):
    idempotency_key:str=Field(min_length=1,max_length=100)
    items:list[SyncItem]=Field(min_length=1,max_length=100)
