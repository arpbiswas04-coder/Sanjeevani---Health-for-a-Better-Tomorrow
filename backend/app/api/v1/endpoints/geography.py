from app.schemas import outputs as out
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User, Facility
from app.schemas.geography import GeographyCreate, FacilityUpdate
from app.services import geography
from app.security.auth import require
from app.security.scope import check_facility, global_only
from app.repositories.common import get_record, serialize

router = APIRouter(responses=out.ERROR_RESPONSES, tags=['Geography and facilities'])


@router.post('/geography/{kind}', status_code=201, response_model=out.Success[out.Geography], response_model_exclude_unset=True)
async def create_geography(kind: Literal['countries','states','districts','blocks'], payload: GeographyCreate,
                           db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('facility.manage'))):
    global_only(user)
    return {'success': True, 'data': await geography.create_geography(db, user, kind, payload)}


@router.get('/geography/{kind}', response_model=out.Success[list[out.Geography]], response_model_exclude_unset=True)
async def list_geography(kind: Literal['countries','states','districts','blocks'], parent_id: UUID | None = None,
                         offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                         db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    model, parent, field = geography.GEOGRAPHIES[kind]
    query = select(model)
    if parent_id and field:
        query = query.where(getattr(model, field) == parent_id)
    rows = await db.scalars(query.order_by(model.id).offset(offset).limit(limit))
    return {'success': True, 'data': [serialize(row) for row in rows]}


@router.get('/facilities', response_model=out.Success[list[out.FacilityView]], response_model_exclude_unset=True)
async def facilities(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                     search: str | None = Query(None, max_length=200), block_id: UUID | None = None,
                     district_id: UUID | None = None, state_id: UUID | None = None, country_id: UUID | None = None,
                     active: bool | None = True, db: AsyncSession = Depends(get_db, scope="function"),
                     user: User = Depends(require('inventory.read'))):
    return {'success': True, 'data': await geography.list_facilities(db, user, offset, limit, search, block_id, district_id, state_id, country_id, active)}


@router.get('/facilities/nearby', response_model=out.Success[list[out.NearbyFacility]], response_model_exclude_unset=True)
async def nearby(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180),
                  radius_km: float = Query(10, gt=0, le=500), limit: int = Query(50, ge=1, le=200),
                  db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    return {'success': True, 'data': await geography.nearby(db, user, latitude, longitude, radius_km, limit)}


@router.get('/facilities/{identifier}', response_model=out.Success[out.FacilityView], response_model_exclude_unset=True)
async def facility(identifier: UUID, db: AsyncSession = Depends(get_db, scope="function"), user: User = Depends(require('inventory.read'))):
    await check_facility(db, user, identifier)
    return {'success': True, 'data': serialize(await get_record(db, Facility, identifier))}


@router.patch('/facilities/{identifier}', response_model=out.Success[out.FacilityView], response_model_exclude_unset=True)
async def update_facility(identifier: UUID, payload: FacilityUpdate, db: AsyncSession = Depends(get_db, scope="function"),
                          user: User = Depends(require('facility.manage'))):
    return {'success': True, 'data': await geography.update_facility(db, user, identifier, payload)}
