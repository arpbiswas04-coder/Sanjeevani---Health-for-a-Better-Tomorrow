from fastapi import HTTPException
from app.models import Facility,Medicine
from app.repositories.common import get_record,serialize
from app.services.inventory import audit


async def create(db,user,model,payload):
    row=model(**payload.model_dump())
    db.add(row)
    await db.flush()
    audit(db,user.id,'facility.create' if model is Facility else 'medicine.create',{'id':str(row.id)})
    return serialize(row)


async def update_medicine(db,user,identifier,payload):
    row=await get_record(db,Medicine,identifier,lock=True)
    values=payload.model_dump(exclude_unset=True)
    if any(v is None for v in values.values()):
        raise HTTPException(422,'Medicine fields cannot be null')
    for key,value in values.items():
        setattr(row,key,value)
    audit(db,user.id,'medicine.updated',{'id':str(identifier),'fields':list(values)})
    await db.flush()
    return serialize(row)
