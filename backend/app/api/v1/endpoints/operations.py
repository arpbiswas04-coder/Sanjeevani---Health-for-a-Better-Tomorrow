from app.schemas import outputs as out
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.models.operations import TemperatureObservation,BedCapacity,BedOccupancyHistory,Staff,StaffRole,Shift,Attendance,PatientFootfall,DiseaseCount
from app.schemas.operations import TemperatureInput,BedInput,StaffInput,StaffRoleInput,ShiftInput,AttendanceInput,AggregateInput
from app.security.auth import require,current_user
from app.security.scope import check_facility,global_only
from app.services import operations
from app.services.inventory import audit
from app.repositories.common import serialize,get_record

router=APIRouter(responses=out.ERROR_RESPONSES, tags=['Operations'])


def data(value):
    return {'success':True,'data':value}


@router.post('/cold-chain/observations',status_code=201, response_model=out.Success[out.TemperatureObservationView], response_model_exclude_unset=True)
async def temperature(payload:TemperatureInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('inventory.write'))):
    return data(await operations.temperature(db,user,payload))


@router.put('/beds', response_model=out.Success[out.BedsAvailable], response_model_exclude_unset=True)
async def beds(payload:BedInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('beds.write'))):
    return data(await operations.bed_update(db,user,payload))


@router.get('/beds/{identifier}/history', response_model=out.Success[list[out.BedOccupancyHistoryView]], response_model_exclude_unset=True)
async def bed_history(identifier:UUID,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('beds.read'))):
    bed=await get_record(db,BedCapacity,identifier)
    await check_facility(db,user,bed.facility_id)
    return data([serialize(r) for r in await db.scalars(select(BedOccupancyHistory).where(BedOccupancyHistory.bed_id==identifier).order_by(BedOccupancyHistory.created_at).offset(offset).limit(limit))])


@router.post('/staff-roles',status_code=201, response_model=out.Success[out.StaffRoleView], response_model_exclude_unset=True)
async def staff_role(payload:StaffRoleInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('workforce.write'))):
    global_only(user)
    row=StaffRole(**payload.model_dump())
    db.add(row)
    await db.flush()
    audit(db,user.id,'staff_role.created',{'id':str(row.id)})
    return data(serialize(row))


@router.get('/staff-roles', response_model=out.Success[list[out.StaffRoleView]], response_model_exclude_unset=True)
async def staff_roles(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('workforce.read'))):
    return data([serialize(r) for r in await db.scalars(select(StaffRole).order_by(StaffRole.id).offset(offset).limit(limit))])


@router.post('/staff',status_code=201, response_model=out.Success[out.StaffView], response_model_exclude_unset=True)
async def staff(payload:StaffInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('workforce.write'))):
    return data(await operations.staff_save(db,user,payload))


@router.put('/staff/{identifier}', response_model=out.Success[out.StaffView], response_model_exclude_unset=True)
async def update_staff(identifier:UUID,payload:StaffInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('workforce.write'))):
    return data(await operations.staff_save(db,user,payload,identifier))


@router.post('/shifts',status_code=201, response_model=out.Success[out.ShiftView], response_model_exclude_unset=True)
async def shift(payload:ShiftInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('workforce.write'))):
    return data(await operations.shift_create(db,user,payload))


@router.post('/attendance',status_code=201, response_model=out.Success[out.AttendanceView], response_model_exclude_unset=True)
async def attendance(payload:AttendanceInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('workforce.write'))):
    return data(await operations.attendance(db,user,payload))


@router.put('/aggregates/{kind}', response_model=out.Success[out.Aggregate], response_model_exclude_unset=True)
async def aggregate(kind:Literal['footfall','disease-counts'],payload:AggregateInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.write'))):
    return data(await operations.aggregate(db,user,kind,payload))


@router.get('/operations/{kind}', response_model=out.Success[list[out.Operation]], response_model_exclude_unset=True)
async def listing(kind:Literal['temperatures','beds','staff','shifts','attendance','footfall','disease-counts'],facility_id:UUID,
                  offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(current_user)):
    models={'temperatures':(TemperatureObservation,'inventory.read'),'beds':(BedCapacity,'beds.read'),
            'staff':(Staff,'workforce.read'),'shifts':(Shift,'workforce.read'),'attendance':(Attendance,'workforce.read'),
            'footfall':(PatientFootfall,'integration.read'),'disease-counts':(DiseaseCount,'integration.read')}
    model,permission=models[kind]
    await require(permission)(user,db)
    await check_facility(db,user,facility_id)
    rows=await db.scalars(select(model).where(model.facility_id==facility_id).order_by(model.id).offset(offset).limit(limit))
    return data([{**serialize(r),**({'available':r.capacity-r.occupied} if kind=='beds' else {})} for r in rows])

@router.post('/shifts/{identifier}/cancel', response_model=out.Success[out.ShiftView], response_model_exclude_unset=True)
async def cancel_shift(identifier:UUID,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('workforce.write'))):
    return data(await operations.cancel_shift(db,user,identifier))


from pydantic import AwareDatetime


@router.get('/cold-chain/series',response_model=out.Success[list[out.ColdChainSampleView]])
async def cold_chain_series(facility_id:UUID,start:AwareDatetime,end:AwareDatetime,
    offset:int=Query(0,ge=0),limit:int=Query(200,ge=1,le=1000),db:AsyncSession=Depends(get_db,scope='function'),
    user:User=Depends(require('inventory.read'))):
    return data(await operations.cold_chain_series(db,user,facility_id,start,end,offset,limit))
