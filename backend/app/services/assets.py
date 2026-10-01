from fastapi import HTTPException
from app.models.assets import Equipment,MaintenanceRecord
from app.repositories.common import get_record,serialize
from app.security.scope import check_facility
from app.services.inventory import audit


async def save(db,user,model,payload,identifier=None):
    await check_facility(db,user,payload.facility_id)
    row=await get_record(db,model,identifier,lock=True) if identifier else model()
    if identifier:
        await check_facility(db,user,row.facility_id)
    for k,v in payload.model_dump().items():
        setattr(row,k,v)
    db.add(row)
    await db.flush()
    audit(db,user.id,model.__tablename__+'.saved',{'id':str(row.id)})
    return serialize(row)


async def maintain(db,user,identifier,payload):
    equipment=await get_record(db,Equipment,identifier,lock=True)
    await check_facility(db,user,equipment.facility_id)
    if equipment.last_maintenance and payload.performed_on<equipment.last_maintenance:
        raise HTTPException(409,'Maintenance predates the latest record')
    row=MaintenanceRecord(equipment_id=identifier,actor_id=user.id,**payload.model_dump())
    db.add(row)
    equipment.last_maintenance=payload.performed_on
    equipment.next_maintenance=payload.next_due
    await db.flush()
    audit(db,user.id,'equipment.maintained',{'id':str(identifier),'record_id':str(row.id)})
    return serialize(row)
