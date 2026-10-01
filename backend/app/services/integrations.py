from datetime import datetime,timezone,timedelta
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Facility,Medicine,MedicineBatch
from app.models.geography import District
from app.models.integrations import Recommendation,PopulationSnapshot,WeatherCache,Barcode,BackupRecord
from app.repositories.common import get_record,serialize
from app.security.scope import check_facility
from app.services.inventory import audit
from app.services.identity import aware
from app.services.transfers import create as transfer_create
from app.schemas.transfers import TransferCreate
from app.integrations.weather import fetch_weather
from app.core.config import settings


async def recommendation_create(db,user,payload):
    await check_facility(db,user,payload.source_id)
    await check_facility(db,user,payload.destination_id)
    for item in payload.items:
        await get_record(db,MedicineBatch,item.batch_id)
    row=Recommendation(source_id=payload.source_id,destination_id=payload.destination_id,submitted_by=user.id,
                       model_version=payload.model_version,payload=payload.model_dump(mode='json'))
    db.add(row)
    await db.flush()
    audit(db,user.id,'recommendation.created',{'id':str(row.id)})
    return serialize(row)


async def recommendation_action(db,user,identifier,payload):
    row=await get_record(db,Recommendation,identifier,lock=True)
    await check_facility(db,user,row.source_id)
    await check_facility(db,user,row.destination_id)
    if payload.action in ('approve','reject') and row.status=='proposed':
        row.status='approved' if payload.action=='approve' else 'rejected'
    elif payload.action=='apply' and row.status=='approved':
        result=await transfer_create(db,user,TransferCreate(source_id=row.source_id,destination_id=row.destination_id,
            reference='recommendation:'+str(row.id),items=row.payload['items'],idempotency_key='recommendation:'+str(row.id)))
        from uuid import UUID
        row.transfer_id=UUID(str(result['id']))
        row.status='applied'
    else:
        raise HTTPException(409,'Invalid recommendation transition')
    audit(db,user.id,'recommendation.'+payload.action,{'id':str(row.id),'transfer_id':str(row.transfer_id) if row.transfer_id else None})
    await db.flush()
    return serialize(row)


async def weather(db,user,facility_id):
    await check_facility(db,user,facility_id)
    facility=await get_record(db,Facility,facility_id,lock=True)
    if facility.latitude is None or facility.longitude is None:
        raise HTTPException(409,'Facility location is unavailable')
    row=await db.scalar(select(WeatherCache).where(WeatherCache.facility_id==facility_id))
    now=datetime.now(timezone.utc)
    if row and row.latitude==facility.latitude and row.longitude==facility.longitude and (now-aware(row.retrieved_at)).total_seconds()<settings.WEATHER_CACHE_SECONDS:
        return {**row.payload,'retrieved_at':row.retrieved_at,'cached':True}
    try:
        payload=await fetch_weather(facility.latitude,facility.longitude)
    except Exception:
        raise HTTPException(503,'Weather provider unavailable or response invalid')
    if row is None:
        row=WeatherCache(facility_id=facility_id)
        db.add(row)
    row.latitude,row.longitude=facility.latitude,facility.longitude
    row.retrieved_at,row.payload=now,payload
    return {**payload,'retrieved_at':now,'cached':False}


async def population(db,user,payload):
    await get_record(db,District,payload.district_id)
    now=datetime.now(timezone.utc)
    if payload.as_of>now.date() or payload.retrieved_at>now:
        raise HTTPException(422,'Population provenance cannot be future-dated')
    if payload.source_url.username or payload.source_url.password or payload.source_url.query:
        raise HTTPException(422,'Use a public provenance URL without credentials or query tokens')
    values=payload.model_dump()
    values['source_url']=str(payload.source_url)
    row=PopulationSnapshot(**values)
    db.add(row)
    await db.flush()
    audit(db,user.id,'population.imported',{'id':str(row.id),'source':row.source})
    return serialize(row)


async def barcode(db,user,payload):
    await get_record(db,Medicine if payload.medicine_id else MedicineBatch,payload.medicine_id or payload.batch_id)
    row=Barcode(**payload.model_dump())
    db.add(row)
    await db.flush()
    audit(db,user.id,'barcode.created',{'id':str(row.id)})
    return serialize(row)


async def backup(db,user,payload):
    now=datetime.now(timezone.utc)
    if any(value and value>now for value in (payload.started_at,payload.completed_at,payload.verified_at)):
        raise HTTPException(422,'Backup timestamps cannot be in the future')
    row=BackupRecord(**payload.model_dump())
    db.add(row)
    await db.flush()
    audit(db,user.id,'backup.recorded',{'id':str(row.id),'status':row.status})
    return serialize(row)


async def backup_status(db):
    latest=await db.scalar(select(BackupRecord).where(BackupRecord.status=='completed').order_by(BackupRecord.completed_at.desc()).limit(1))
    age=(datetime.now(timezone.utc)-aware(latest.completed_at)).total_seconds()/3600 if latest else None
    return {'latest':serialize(latest) if latest else None,'healthy':age is not None and age<=settings.BACKUP_MAX_AGE_HOURS,
            'retention_days':settings.BACKUP_RETENTION_DAYS,'storage_name':settings.BACKUP_STORAGE_NAME,
            'verification_reported':bool(latest and latest.verified_at),'execution_owner':'Member 4 infrastructure'}
