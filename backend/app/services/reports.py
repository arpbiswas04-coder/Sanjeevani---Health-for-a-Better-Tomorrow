from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select,and_,func
from app.models import Inventory,MedicineBatch,Facility,Medicine
from app.models.geography import Block,District,State
from app.models.transfers import TransferRequest
from app.models.supply import PurchaseOrder
from app.models.operations import Staff,BedCapacity
from app.models.alerts import Alert
from app.repositories.common import serialize
from app.security.scope import facility_filter
from app.models.stock import StockPolicy
from app.services.stock import expiry_cutoff
from app.core.time import utc_today

MODELS={'stock':Inventory,'expiry':Inventory,'transfers':TransferRequest,'procurement':PurchaseOrder,'staff':Staff,'beds':BedCapacity,'emergency':Alert}


async def report(db,user,kind,offset,limit,facility_id=None,medicine_id=None,status=None,start=None,end=None,district_id=None,state_id=None):
    if start and end and start>end:
        raise HTTPException(422,'Start must not follow end')
    model=MODELS[kind]
    facility_column=model.source_id if kind=='transfers' else model.facility_id
    query=select(model).where(facility_filter(user,facility_column))
    if kind=='transfers':
        query=query.where(facility_filter(user,model.destination_id))
    if facility_id:
        query=query.where(facility_column==facility_id)
    if kind in ('stock','expiry'):
        query=select(Inventory,MedicineBatch,Medicine,Facility).join(MedicineBatch,Inventory.batch_id==MedicineBatch.id).join(
            Medicine,MedicineBatch.medicine_id==Medicine.id).join(Facility,Inventory.facility_id==Facility.id).outerjoin(
            StockPolicy,and_(StockPolicy.facility_id==Inventory.facility_id,StockPolicy.medicine_id==Medicine.id)).where(
            facility_filter(user,Inventory.facility_id))
        if facility_id:
            query=query.where(Inventory.facility_id==facility_id)
        if medicine_id:
            query=query.where(MedicineBatch.medicine_id==medicine_id)
        if kind=='expiry':
            query=query.where(Inventory.quantity>0,MedicineBatch.expires_on<=expiry_cutoff(db,func.coalesce(StockPolicy.expiry_warning_days,90)))
    elif medicine_id:
        raise HTTPException(422,'Medicine filter applies to stock and expiry reports')
    if status and kind=='expiry':
        if status not in ('expired','upcoming'):
            raise HTTPException(422,'Expiry status must be expired or upcoming')
        query=query.where(MedicineBatch.expires_on<=utc_today() if status=='expired' else MedicineBatch.expires_on>utc_today())
    elif status:
        if not hasattr(model,'status'):
            raise HTTPException(422,'Status filter is unavailable for this report')
        query=query.where(model.status==status)
    if kind=='emergency':
        query=query.where(Alert.severity=='critical')
    if start:
        query=query.where(model.created_at>=start)
    if end:
        query=query.where(model.created_at<end)
    if district_id or state_id:
        if kind not in ('stock','expiry'):
            query=query.join(Facility,facility_column==Facility.id)
        query=query.join(Block,Facility.block_id==Block.id).join(District).join(State)
        if district_id:
            query=query.where(District.id==district_id)
        if state_id:
            query=query.where(State.id==state_id)
    query=query.order_by(model.created_at,model.id).offset(offset).limit(limit+1)
    if kind in ('stock','expiry'):
        rows=list((await db.execute(query)).all())
        result=[{**serialize(i),'medicine_id':m.id,'medicine_name':m.name,'medicine_code':m.code,'unit':m.unit,
            'batch_number':b.batch_number,'expires_on':b.expires_on,'recalled':b.recalled,
            'facility_name':f.name,'facility_code':f.code,'available':i.quantity-i.reserved if not b.recalled and b.expires_on>utc_today() else 0,
            'expiry_state':'expired' if b.expires_on<=utc_today() else 'upcoming'} for i,b,m,f in rows[:limit]]
    else:
        rows=list(await db.scalars(query))
        result=[serialize(row) for row in rows[:limit]]
    return {'rows':result,'has_more':len(rows)>limit,'offset':offset,'limit':limit}
