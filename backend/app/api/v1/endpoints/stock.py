from app.schemas import outputs as out
from app.core.time import utc_today
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User, Inventory, MedicineBatch
from app.models.stock import RecallRecord
from app.schemas.stock import Adjustment, PolicyInput, RecallInput, RecallResolution
from app.security.auth import require
from app.security.scope import check_facility, global_only
from app.services import stock
from app.services.inventory import audit
from app.repositories.common import serialize, get_record

router = APIRouter(responses=out.ERROR_RESPONSES, tags=['Stock policies and traceability'])


@router.post('/inventory/adjust', response_model=out.Success[out.Adjusted], response_model_exclude_unset=True)
async def adjust(payload: Adjustment, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.write'))):
    return {'success': True, 'data': await stock.adjust(db, user, payload)}


@router.put('/inventory/policies/{facility_id}/{medicine_id}', response_model=out.Success[out.StockPolicyView], response_model_exclude_unset=True)
async def policy(facility_id: UUID, medicine_id: UUID, payload: PolicyInput, db: AsyncSession = Depends(get_db, scope="function"),
                 user: User = Depends(require('admin.config'))):
    return {'success': True, 'data': await stock.set_policy(db, user, facility_id, medicine_id, payload)}


@router.get('/inventory/days-of-stock', response_model=out.Success[out.DaysOfStock], response_model_exclude_unset=True)
async def dos(facility_id: UUID, medicine_id: UUID, window: int = Query(30, ge=1, le=365),
              db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    return {'success': True, 'data': await stock.days_of_stock(db, user, facility_id, medicine_id, window)}


@router.get('/inventory/expiry', response_model=out.Success[list[out.Expiry]], response_model_exclude_unset=True)
async def expiry(facility_id: UUID, days: int | None = Query(None, ge=0, le=3650), offset: int = Query(0, ge=0),
                 limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    return {'success':True,'data':await stock.expiry_rows(db,user,facility_id,days,offset,limit)}


@router.post('/recalls', status_code=201, response_model=out.Success[out.RecallRecordView], response_model_exclude_unset=True)
async def recall(payload: RecallInput, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.recall'))):
    global_only(user)
    return {'success': True, 'data': await stock.recall(db, user, payload)}


@router.post('/recalls/{identifier}/resolve', response_model=out.Success[out.RecallRecordView], response_model_exclude_unset=True)
async def resolve(identifier: UUID, payload: RecallResolution, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.recall'))):
    global_only(user)
    row = await get_record(db, RecallRecord, identifier, lock=True)
    if row.status!='active':
        raise HTTPException(409,'Recall is already resolved')
    row.status, row.resolution = 'resolved', payload.resolution
    audit(db, user.id, 'recall.resolved', {'id': str(identifier)})
    # Resolution records disposition; it never releases recalled stock for issue.
    await db.flush()
    return {'success': True, 'data': serialize(row)}


@router.get('/batches/{identifier}/trace', response_model=out.Success[out.Trace], response_model_exclude_unset=True)
async def trace(identifier: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    return {'success': True, 'data': await stock.trace(db, user, identifier, offset, limit)}

@router.get('/recalls', response_model=out.Success[list[out.RecallRecordView]], response_model_exclude_unset=True)
async def recall_records(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('inventory.read'))):
    rows=await db.scalars(select(RecallRecord).order_by(RecallRecord.created_at,RecallRecord.id).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(row) for row in rows]}
