from datetime import datetime,timezone
from sqlalchemy import select,func
from fastapi import HTTPException
from app.models import Inventory,MedicineBatch,StockTransaction,Facility
from app.models.operations import PatientFootfall,DiseaseCount
from app.security.scope import check_facility
from app.repositories.common import serialize


async def get_medicine_training_data(db,user,facility_id,medicine_id,start_date,end_date,offset=0,limit=200):
    await check_facility(db,user,facility_id)
    if end_date<start_date or (end_date-start_date).days>365:
        raise HTTPException(422,'Training interval must be ordered and at most 365 days')
    day=func.date(func.timezone('UTC',StockTransaction.created_at)) if db.bind.dialect.name=='postgresql' else func.date(StockTransaction.created_at)
    query=select(day.label('day'),(-func.sum(StockTransaction.quantity)).label('consumed')).join(Inventory).join(MedicineBatch).where(
        Inventory.facility_id==facility_id,MedicineBatch.medicine_id==medicine_id,StockTransaction.kind=='issue',
        day>=str(start_date),day<=str(end_date)).group_by(day).order_by(day).offset(offset).limit(limit)
    return [{'day':str(d),'consumed':q} for d,q in await db.execute(query)]


async def dataset(db,user,kind,facility_id,start_date,end_date,offset,limit):
    await check_facility(db,user,facility_id)
    if end_date<start_date or (end_date-start_date).days>365:
        raise HTTPException(422,'Dataset interval must be ordered and at most 365 days')
    model=PatientFootfall if kind=='footfall' else DiseaseCount
    return [serialize(r) for r in await db.scalars(select(model).where(model.facility_id==facility_id,model.day>=start_date,model.day<=end_date)
            .order_by(model.day,model.id).offset(offset).limit(limit))]
