from app.schemas import outputs as out
from uuid import UUID
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.models.report_jobs import ReportJob,ReportSchedule
from app.schemas.report_jobs import ReportRequest,ScheduleRequest
from app.security.auth import require
from app.repositories.common import get_record,serialize
from app.services import report_jobs
from app.services.identity import aware
from app.services.inventory import audit

router=APIRouter(responses=out.ERROR_RESPONSES, tags=['Background reports'])


@router.post('/report-jobs',status_code=202, response_model=out.Success[out.ReportJobView], response_model_exclude_unset=True)
async def request(payload:ReportRequest,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('reports.export'))):
    return {'success':True,'data':await report_jobs.request(db,user,payload)}


@router.post('/report-schedules',status_code=201, response_model=out.Success[out.ReportScheduleView], response_model_exclude_unset=True)
async def schedule(payload:ScheduleRequest,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('reports.export'))):
    return {'success':True,'data':await report_jobs.request(db,user,payload,True)}


@router.delete('/report-schedules/{identifier}', response_model=out.Success[None], response_model_exclude_unset=True)
async def cancel(identifier:UUID,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('reports.export'))):
    row=await get_record(db,ReportSchedule,identifier,lock=True)
    if row.owner_id!=user.id:
        raise HTTPException(404,'Schedule not found')
    row.active=False
    audit(db,user.id,'report.schedule_cancelled',{'id':str(row.id)})
    return {'success':True,'data':None}


@router.get('/report-jobs/{identifier}', response_model=out.Success[out.ReportJobView], response_model_exclude_unset=True)
async def status(identifier:UUID,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('reports.export'))):
    row=await get_record(db,ReportJob,identifier)
    if row.owner_id!=user.id:
        raise HTTPException(404,'Report job not found')
    await report_jobs.authorize(db,user,row.facility_id,row.kind)
    return {'success':True,'data':serialize(row,('content',))}


@router.get('/report-jobs/{identifier}/download', response_class=Response, responses={200:{'content':out.BINARY_CONTENT}})
async def download(identifier:UUID,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('reports.export'))):
    row=await get_record(db,ReportJob,identifier)
    if row.owner_id!=user.id:
        raise HTTPException(404,'Report job not found')
    await report_jobs.authorize(db,user,row.facility_id,row.kind)
    if row.status!='completed' or aware(row.expires_at)<=datetime.now(timezone.utc):
        raise HTTPException(409,'Report is unavailable or expired')
    return Response(row.content,media_type=row.media_type,headers={'Content-Disposition':f'attachment; filename="{row.kind}.{row.format}"'})
