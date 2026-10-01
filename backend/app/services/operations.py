from fastapi import HTTPException
from sqlalchemy import select
from app.models import Facility
from app.models.supply import Shipment
from app.models.operations import TemperatureObservation,BedCapacity,BedOccupancyHistory,Staff,StaffRole,Shift,Attendance,PatientFootfall,DiseaseCount
from app.repositories.common import get_record,serialize
from app.security.scope import check_facility
from app.services.inventory import audit


async def temperature(db,user,payload):
    await check_facility(db,user,payload.facility_id)
    await get_record(db,Facility,payload.facility_id,lock=True)
    if payload.shipment_id:
        shipment=await get_record(db,Shipment,payload.shipment_id)
        if shipment.facility_id!=payload.facility_id:
            raise HTTPException(422,'Shipment destination does not match facility')
    existing=await db.scalar(select(TemperatureObservation).where(TemperatureObservation.source==payload.source,TemperatureObservation.external_id==payload.external_id))
    if existing:
        # Same source event is immutable; reject conflicting retries.
        from app.services.identity import aware
        values=payload.model_dump()
        if any((aware(getattr(existing,k)) if k=='observed_at' else getattr(existing,k))!=v for k,v in values.items()):
            raise HTTPException(409,'Observation event already exists with different input')
        return serialize(existing)
    row=TemperatureObservation(**payload.model_dump(),excursion=not payload.minimum<=payload.temperature<=payload.maximum)
    db.add(row)
    await db.flush()
    from app.models.operations import ColdChainSample
    db.add(ColdChainSample(id=row.id,observed_at=row.observed_at,facility_id=row.facility_id,temperature=row.temperature,
        minimum=row.minimum,maximum=row.maximum,excursion=row.excursion))
    audit(db,user.id,'cold_chain.observed',{'id':str(row.id),'excursion':row.excursion})
    return serialize(row)


async def bed_update(db,user,payload):
    await check_facility(db,user,payload.facility_id)
    await get_record(db,Facility,payload.facility_id,lock=True)
    row=await db.scalar(select(BedCapacity).where(BedCapacity.facility_id==payload.facility_id,BedCapacity.bed_type==payload.bed_type))
    if not row:
        row=BedCapacity(**payload.model_dump())
        db.add(row)
    row.capacity,row.occupied=payload.capacity,payload.occupied
    await db.flush()
    db.add(BedOccupancyHistory(bed_id=row.id,capacity=row.capacity,occupied=row.occupied,actor_id=user.id))
    audit(db,user.id,'beds.updated',{'id':str(row.id),'capacity':row.capacity,'occupied':row.occupied})
    return {**serialize(row),'available':row.capacity-row.occupied}


async def staff_save(db,user,payload,identifier=None):
    await check_facility(db,user,payload.facility_id)
    await get_record(db,StaffRole,payload.staff_role_id)
    row=await get_record(db,Staff,identifier,lock=True) if identifier else Staff()
    if identifier:
        await check_facility(db,user,row.facility_id)
    for k,v in payload.model_dump().items():
        setattr(row,k,v)
    db.add(row)
    await db.flush()
    audit(db,user.id,'staff.saved',{'id':str(row.id)})
    return serialize(row)


async def shift_create(db,user,payload):
    staff=await get_record(db,Staff,payload.staff_id,lock=True)
    await check_facility(db,user,staff.facility_id)
    if not staff.active:
        raise HTTPException(409,'Staff member is inactive')
    overlap=await db.scalar(select(Shift.id).where(Shift.staff_id==staff.id,Shift.cancelled.is_(False),Shift.starts_at<payload.ends_at,Shift.ends_at>payload.starts_at))
    if overlap:
        raise HTTPException(409,'Shift overlaps an existing shift')
    row=Shift(**payload.model_dump(),facility_id=staff.facility_id)
    db.add(row)
    await db.flush()
    audit(db,user.id,'shift.created',{'id':str(row.id)})
    return serialize(row)


async def attendance(db,user,payload):
    staff=await get_record(db,Staff,payload.staff_id,lock=True)
    await check_facility(db,user,staff.facility_id)
    row=await db.scalar(select(Attendance).where(Attendance.staff_id==staff.id,Attendance.day==payload.day))
    if row:
        raise HTTPException(409,'Attendance already recorded for this day')
    row=Attendance(**payload.model_dump(),facility_id=staff.facility_id)
    db.add(row)
    await db.flush()
    audit(db,user.id,'attendance.recorded',{'id':str(row.id)})
    return serialize(row)


async def aggregate(db,user,kind,payload):
    from app.services.sync_log import lock_clock, append_change
    await lock_clock(db)
    await check_facility(db,user,payload.facility_id)
    await get_record(db,Facility,payload.facility_id,lock=True)
    model=PatientFootfall if kind=='footfall' else DiseaseCount
    row=await db.scalar(select(model).where(model.facility_id==payload.facility_id,model.day==payload.day,model.category==payload.category))
    if row:
        if row.version!=payload.expected_version:
            raise HTTPException(409,'Aggregate version conflict')
        row.version+=1
        row.count,row.source_device=payload.count,payload.source_device
    else:
        if payload.expected_version!=0:
            raise HTTPException(409,'Aggregate does not exist')
        row=model(**payload.model_dump(exclude={'expected_version'}))
        db.add(row)
    await db.flush()
    audit(db,user.id,kind+'.recorded',{'id':str(row.id),'version':row.version})
    await append_change(db,kind,row)
    return serialize(row)

async def cancel_shift(db,user,identifier):
    row=await get_record(db,Shift,identifier,lock=True)
    await check_facility(db,user,row.facility_id)
    if row.cancelled:
        raise HTTPException(409,'Shift is already cancelled')
    row.cancelled=True
    audit(db,user.id,'shift.cancelled',{'id':str(row.id)})
    await db.flush()
    return serialize(row)


async def cold_chain_series(db,user,facility_id,start,end,offset,limit):
    from app.models.operations import ColdChainSample
    from app.services.identity import aware
    await check_facility(db,user,facility_id)
    if end<=start or (end-start).days>366:
        raise HTTPException(422,'Series interval must be ordered and at most 366 days')
    rows=await db.scalars(select(ColdChainSample).where(ColdChainSample.facility_id==facility_id,
        ColdChainSample.observed_at>=start,ColdChainSample.observed_at<end)
        .order_by(ColdChainSample.observed_at,ColdChainSample.id).offset(offset).limit(limit))
    return [serialize(row) for row in rows]
