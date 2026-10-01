from app.schemas import outputs as out
from datetime import date
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User,Facility
from app.models.integrations import Recommendation,PopulationSnapshot,Barcode
from app.schemas.integrations import RecommendationInput,RecommendationAction,PopulationInput,BarcodeInput,BackupInput
from app.security.auth import require
from app.security.scope import check_facility,facility_filter,global_only
from app.repositories.common import get_record,serialize
from app.services import integrations,datasets,stock
from app.integrations.fhir import facility_location

router=APIRouter(responses=out.ERROR_RESPONSES, tags=['Integration contracts'])


def data(value):
    return {'success':True,'data':value}


@router.get('/integrations/fhir/locations/{identifier}', response_model=out.Success[out.Location], response_model_exclude_unset=True)
async def fhir(identifier:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    await check_facility(db,user,identifier)
    return data(facility_location(await get_record(db,Facility,identifier)))


@router.get('/datasets/medicine-consumption', response_model=out.Success[list[out.Consumption]], response_model_exclude_unset=True)
async def consumption(facility_id:UUID,medicine_id:UUID,start_date:date,end_date:date,offset:int=Query(0,ge=0),limit:int=Query(200,ge=1,le=500),
                       db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    return data(await datasets.get_medicine_training_data(db,user,facility_id,medicine_id,start_date,end_date,offset,limit))


@router.get('/datasets/{kind}', response_model=out.Success[list[out.Aggregate]], response_model_exclude_unset=True)
async def dataset(kind:Literal['footfall','disease-counts'],facility_id:UUID,start_date:date,end_date:date,
                   offset:int=Query(0,ge=0),limit:int=Query(200,ge=1,le=500),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    return data(await datasets.dataset(db,user,kind,facility_id,start_date,end_date,offset,limit))


@router.get('/optimization/context', response_model=out.Success[out.OptimizationContext], response_model_exclude_unset=True)
async def optimization_context(facility_id:UUID,medicine_id:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    await check_facility(db,user,facility_id)
    facility=await get_record(db,Facility,facility_id)
    return data({'facility':serialize(facility),'stock':await stock.days_of_stock(db,user,facility_id,medicine_id),
                 'predicted_demand':None,'transport_metadata':None})


@router.post('/optimization/recommendations',status_code=201, response_model=out.Success[out.RecommendationView], response_model_exclude_unset=True)
async def recommendation(payload:RecommendationInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.write'))):
    return data(await integrations.recommendation_create(db,user,payload))


@router.get('/optimization/recommendations', response_model=out.Success[list[out.RecommendationView]], response_model_exclude_unset=True)
async def recommendations(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    rows=await db.scalars(select(Recommendation).where(facility_filter(user,Recommendation.source_id),facility_filter(user,Recommendation.destination_id))
                          .order_by(Recommendation.id).offset(offset).limit(limit))
    return data([serialize(r) for r in rows])


@router.post('/optimization/recommendations/{identifier}/actions', response_model=out.Success[out.RecommendationView], response_model_exclude_unset=True)
async def recommendation_action(identifier:UUID,payload:RecommendationAction,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('inventory.transfer'))):
    return data(await integrations.recommendation_action(db,user,identifier,payload))


@router.get('/integrations/weather/{facility_id}', response_model=out.Success[out.Weather], response_model_exclude_unset=True)
async def weather(facility_id:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    return data(await integrations.weather(db,user,facility_id))


@router.post('/integrations/population',status_code=201, response_model=out.Success[out.PopulationSnapshotView], response_model_exclude_unset=True)
async def population(payload:PopulationInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.write'))):
    global_only(user)
    return data(await integrations.population(db,user,payload))


@router.get('/integrations/population', response_model=out.Success[list[out.PopulationSnapshotView]], response_model_exclude_unset=True)
async def population_list(district_id:UUID,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('integration.read'))):
    rows=await db.scalars(select(PopulationSnapshot).where(PopulationSnapshot.district_id==district_id).order_by(PopulationSnapshot.as_of).offset(offset).limit(limit))
    return data([serialize(r) for r in rows])


@router.post('/barcodes',status_code=201, response_model=out.Success[out.BarcodeView], response_model_exclude_unset=True)
async def barcode(payload:BarcodeInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('inventory.write'))):
    global_only(user)
    return data(await integrations.barcode(db,user,payload))


@router.get('/barcodes/lookup', response_model=out.Success[out.BarcodeView], response_model_exclude_unset=True)
async def barcode_lookup(code:str=Query(min_length=1,max_length=128),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('inventory.read'))):
    row=await db.scalar(select(Barcode).where(Barcode.code==code))
    if not row:
        raise HTTPException(404,'Barcode not found')
    return data(serialize(row))


@router.post('/admin/backups',status_code=201, response_model=out.Success[out.BackupRecordView], response_model_exclude_unset=True)
async def backup(payload:BackupInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('admin.config'))):
    global_only(user)
    return data(await integrations.backup(db,user,payload))


@router.get('/admin/backups/status', response_model=out.Success[out.BackupStatus], response_model_exclude_unset=True)
async def backup_status(db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('admin.config'))):
    global_only(user)
    return data(await integrations.backup_status(db))
