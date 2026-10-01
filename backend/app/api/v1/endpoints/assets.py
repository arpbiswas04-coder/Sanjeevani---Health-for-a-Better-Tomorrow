from app.schemas import outputs as out
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.models.assets import Equipment,MaintenanceRecord,Ambulance
from app.schemas.assets import EquipmentInput,MaintenanceInput,AmbulanceInput
from app.security.auth import require
from app.security.scope import check_facility
from app.repositories.common import get_record,serialize
from app.services import assets

router=APIRouter(responses=out.ERROR_RESPONSES, tags=['Equipment and ambulances'])


@router.post('/equipment',status_code=201, response_model=out.Success[out.EquipmentView], response_model_exclude_unset=True)
async def create_equipment(payload:EquipmentInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.write'))):
    return {'success':True,'data':await assets.save(db,user,Equipment,payload)}


@router.put('/equipment/{identifier}', response_model=out.Success[out.EquipmentView], response_model_exclude_unset=True)
async def update_equipment(identifier:UUID,payload:EquipmentInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.write'))):
    return {'success':True,'data':await assets.save(db,user,Equipment,payload,identifier)}


@router.post('/equipment/{identifier}/maintenance',status_code=201, response_model=out.Success[out.MaintenanceRecordView], response_model_exclude_unset=True)
async def maintain(identifier:UUID,payload:MaintenanceInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.write'))):
    return {'success':True,'data':await assets.maintain(db,user,identifier,payload)}


@router.get('/equipment/{identifier}/maintenance', response_model=out.Success[list[out.MaintenanceRecordView]], response_model_exclude_unset=True)
async def history(identifier:UUID,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.read'))):
    row=await get_record(db,Equipment,identifier)
    await check_facility(db,user,row.facility_id)
    rows=await db.scalars(select(MaintenanceRecord).where(MaintenanceRecord.equipment_id==identifier).order_by(MaintenanceRecord.performed_on).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(r) for r in rows]}


@router.post('/ambulances',status_code=201, response_model=out.Success[out.AmbulanceView], response_model_exclude_unset=True)
async def create_ambulance(payload:AmbulanceInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.write'))):
    return {'success':True,'data':await assets.save(db,user,Ambulance,payload)}


@router.put('/ambulances/{identifier}', response_model=out.Success[out.AmbulanceView], response_model_exclude_unset=True)
async def update_ambulance(identifier:UUID,payload:AmbulanceInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.write'))):
    return {'success':True,'data':await assets.save(db,user,Ambulance,payload,identifier)}


@router.get('/assets/{kind}', response_model=out.Success[list[out.Asset]], response_model_exclude_unset=True)
async def listing(kind:Literal['equipment','ambulances'],facility_id:UUID,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),
                  db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('equipment.read'))):
    await check_facility(db,user,facility_id)
    model=Equipment if kind=='equipment' else Ambulance
    rows=await db.scalars(select(model).where(model.facility_id==facility_id).order_by(model.id).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(r) for r in rows]}
