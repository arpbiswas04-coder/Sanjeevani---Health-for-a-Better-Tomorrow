from uuid import UUID
from pydantic import Field
from app.schemas.platform import Input


class MedicineUpdate(Input):
    name:str|None=Field(None,min_length=1,max_length=200)
    unit:str|None=Field(None,min_length=1,max_length=50)
