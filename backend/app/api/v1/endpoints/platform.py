from uuid import UUID
from app.schemas import outputs as out
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Facility, Medicine, Inventory, MedicineBatch, StockTransaction, User
from app.schemas.platform import FacilityCreate, MedicineCreate, Receive, Issue
from app.security.auth import access_token, current_user, require, verify_password, hasher
from app.services import inventory, identity, catalogue
from app.security.scope import check_facility, facility_filter, global_only

router = APIRouter(responses=out.ERROR_RESPONSES)


def data(value):
    return {'success': True, 'data': value}


def record(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.post('/auth/login', tags=['Authentication'], response_model=out.TokenPair)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db, scope="function"), mfa_proof: str | None = Form(None)):
    return await identity.login(db, form.username, form.password, mfa_proof)


@router.get('/auth/me', tags=['Authentication'], response_model=out.Success[out.Identity])
async def me(user: User = Depends(current_user)):
    return data({'id': user.id, 'username': user.username})


@router.post('/facilities', status_code=201, tags=['Facilities'], response_model=out.Success[out.FacilityView])
async def create_facility(payload: FacilityCreate, db: AsyncSession = Depends(get_db, scope="function"),
                          user: User = Depends(require('facility.manage'))):
    global_only(user)
    return data(await catalogue.create(db, user, Facility, payload))


@router.post('/medicines', status_code=201, tags=['Medicines'], response_model=out.Success[out.MedicineView])
async def create_medicine(payload: MedicineCreate, db: AsyncSession = Depends(get_db, scope="function"),
                          user: User = Depends(require('inventory.write'))):
    global_only(user)
    return data(await catalogue.create(db, user, Medicine, payload))


@router.get('/medicines', tags=['Medicines'], response_model=out.Success[list[out.MedicineView]])
async def medicines(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                    db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    return data([record(row) for row in await db.scalars(select(Medicine).order_by(Medicine.id).offset(offset).limit(limit))])


@router.post('/inventory/receive', status_code=201, tags=['Inventory'], response_model=out.Success[out.Received])
async def receive(payload: Receive, db: AsyncSession = Depends(get_db, scope="function"),
                  user: User = Depends(require('inventory.write'))):
    await check_facility(db, user, payload.facility_id)
    return data(await inventory.receive(db, payload, user))


@router.post('/inventory/issue', tags=['Inventory'], response_model=out.Success[out.Issued])
async def issue(payload: Issue, db: AsyncSession = Depends(get_db, scope="function"),
                user: User = Depends(require('inventory.write'))):
    await check_facility(db, user, payload.facility_id)
    return data(await inventory.issue(db, payload, user))


@router.get('/inventory', tags=['Inventory'], response_model=out.Success[list[out.InventoryWithBatch]])
async def stock(facility_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    await check_facility(db, user, facility_id)
    rows = (await db.execute(select(Inventory, MedicineBatch).join(MedicineBatch)
            .where(Inventory.facility_id == facility_id).order_by(Inventory.id).offset(offset).limit(limit))).all()
    return data([{**record(stock), 'batch': record(batch)} for stock, batch in rows])


@router.get('/inventory/transactions', tags=['Inventory'], response_model=out.Success[list[out.StockTransactionView]])
async def ledger(facility_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                 db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    await check_facility(db, user, facility_id)
    rows = await db.scalars(select(StockTransaction).join(Inventory)
            .where(Inventory.facility_id == facility_id).order_by(StockTransaction.created_at, StockTransaction.id)
            .offset(offset).limit(limit))
    return data([record(row) for row in rows])

from app.schemas.catalogue import MedicineUpdate
from app.repositories.common import get_record,serialize

@router.get('/medicines/{identifier}',tags=['Medicines'], response_model=out.Success[out.MedicineView])
async def medicine_detail(identifier:UUID,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('inventory.read'))):
    return data(serialize(await get_record(db,Medicine,identifier)))


@router.patch('/medicines/{identifier}',tags=['Medicines'], response_model=out.Success[out.MedicineView])
async def medicine_update(identifier:UUID,payload:MedicineUpdate,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('inventory.write'))):
    global_only(user)
    return data(await catalogue.update_medicine(db,user,identifier,payload))
