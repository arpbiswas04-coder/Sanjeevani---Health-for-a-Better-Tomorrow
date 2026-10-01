from app.schemas import outputs as out
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.models.transfers import TransferRequest, TransferItem, TransferTracking
from app.schemas.transfers import TransferCreate, TransferAction
from app.security.auth import require
from app.security.scope import check_facility, facility_filter
from app.services import transfers
from app.repositories.common import serialize, get_record

router = APIRouter(responses=out.ERROR_RESPONSES, prefix='/transfers', tags=['Transfers'])


@router.post('', status_code=201, response_model=out.Success[out.TransferRequestView], response_model_exclude_unset=True)
async def create(payload: TransferCreate, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.transfer'))):
    return {'success': True, 'data': await transfers.create(db, user, payload)}


@router.post('/{identifier}/actions', response_model=out.Success[out.TransferRequestView], response_model_exclude_unset=True)
async def action(identifier: UUID, payload: TransferAction, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.transfer'))):
    return {'success': True, 'data': await transfers.transition(db, user, identifier, payload)}


@router.get('', response_model=out.Success[list[out.TransferRequestView]], response_model_exclude_unset=True)
async def listing(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    rows = await db.scalars(select(TransferRequest).where(facility_filter(user, TransferRequest.source_id), facility_filter(user, TransferRequest.destination_id))
                            .order_by(TransferRequest.id).offset(offset).limit(limit))
    return {'success': True, 'data': [serialize(row) for row in rows]}


@router.get('/{identifier}', response_model=out.Success[out.TransferDetail], response_model_exclude_unset=True)
async def detail(identifier: UUID, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    row = await get_record(db, TransferRequest, identifier)
    await check_facility(db, user, row.source_id)
    await check_facility(db, user, row.destination_id)
    items = await db.scalars(select(TransferItem).where(TransferItem.transfer_id == row.id))
    history = await db.scalars(select(TransferTracking).where(TransferTracking.transfer_id == row.id).order_by(TransferTracking.created_at))
    return {'success': True, 'data': {**serialize(row), 'items': [serialize(i) for i in items], 'history': [serialize(i) for i in history]}}
