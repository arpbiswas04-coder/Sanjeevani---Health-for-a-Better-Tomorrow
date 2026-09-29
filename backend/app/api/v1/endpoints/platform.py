from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Facility, Medicine, Inventory, MedicineBatch, StockTransaction, User
from app.schemas.platform import FacilityCreate, MedicineCreate, Receive, Issue
from app.security.auth import access_token, current_user, require, verify_password, hasher
from app.services import inventory

router = APIRouter()
# Verify a dummy hash on unknown accounts to reduce username timing disclosure.
DUMMY_HASH = hasher.hash('unused-login-timing-password')


def data(value):
    return {'success': True, 'data': value}


def record(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.post('/auth/login', tags=['Authentication'])
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == form.username))
    valid = verify_password(form.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.active:
        raise HTTPException(401, 'Invalid credentials', headers={'WWW-Authenticate': 'Bearer'})
    token = access_token(user.id)
    inventory.audit(db, user.id, 'auth.login', {})
    # OAuth2 token response is intentionally standard for Swagger/client compatibility.
    return {'access_token': token, 'token_type': 'bearer', 'expires_in': 900}


@router.get('/auth/me', tags=['Authentication'])
async def me(user: User = Depends(current_user)):
    return data({'id': user.id, 'username': user.username})


@router.post('/facilities', status_code=201, tags=['Facilities'])
async def create_facility(payload: FacilityCreate, db: AsyncSession = Depends(get_db),
                          user: User = Depends(require('facility.manage'))):
    row = Facility(**payload.model_dump())
    db.add(row)
    await db.flush()
    inventory.audit(db, user.id, 'facility.create', {'id': str(row.id)})
    return data(record(row))


@router.get('/facilities', tags=['Facilities'])
async def facilities(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                     db: AsyncSession = Depends(get_db), user: User = Depends(require('inventory.read'))):
    rows = await db.scalars(select(Facility).where(Facility.active.is_(True)).order_by(Facility.id).offset(offset).limit(limit))
    return data([record(row) for row in rows])


@router.post('/medicines', status_code=201, tags=['Medicines'])
async def create_medicine(payload: MedicineCreate, db: AsyncSession = Depends(get_db),
                          user: User = Depends(require('inventory.write'))):
    row = Medicine(**payload.model_dump())
    db.add(row)
    await db.flush()
    inventory.audit(db, user.id, 'medicine.create', {'id': str(row.id)})
    return data(record(row))


@router.get('/medicines', tags=['Medicines'])
async def medicines(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                    db: AsyncSession = Depends(get_db), user: User = Depends(require('inventory.read'))):
    return data([record(row) for row in await db.scalars(select(Medicine).order_by(Medicine.id).offset(offset).limit(limit))])


@router.post('/inventory/receive', status_code=201, tags=['Inventory'])
async def receive(payload: Receive, db: AsyncSession = Depends(get_db),
                  user: User = Depends(require('inventory.write'))):
    return data(await inventory.receive(db, payload, user))


@router.post('/inventory/issue', tags=['Inventory'])
async def issue(payload: Issue, db: AsyncSession = Depends(get_db),
                user: User = Depends(require('inventory.write'))):
    return data(await inventory.issue(db, payload, user))


@router.get('/inventory', tags=['Inventory'])
async def stock(facility_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                db: AsyncSession = Depends(get_db), user: User = Depends(require('inventory.read'))):
    rows = (await db.execute(select(Inventory, MedicineBatch).join(MedicineBatch)
            .where(Inventory.facility_id == facility_id).order_by(Inventory.id).offset(offset).limit(limit))).all()
    return data([{**record(stock), 'batch': record(batch)} for stock, batch in rows])


@router.get('/inventory/transactions', tags=['Inventory'])
async def ledger(facility_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                 db: AsyncSession = Depends(get_db), user: User = Depends(require('inventory.read'))):
    rows = await db.scalars(select(StockTransaction).join(Inventory)
            .where(Inventory.facility_id == facility_id).order_by(StockTransaction.created_at, StockTransaction.id)
            .offset(offset).limit(limit))
    return data([record(row) for row in rows])
