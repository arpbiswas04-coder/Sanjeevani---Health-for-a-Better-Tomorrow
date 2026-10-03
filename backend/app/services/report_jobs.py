from datetime import datetime,timezone,timedelta
from fastapi import HTTPException
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from app.models import User
from app.models.report_jobs import ReportJob,ReportSchedule
from app.repositories.common import serialize,get_record
from app.security.auth import require
from app.security.scope import check_facility,global_only
from app.services.inventory import audit
from app.services.reports import report
from app.services.exports import export
from app.services.idempotency import replay,remember


async def authorize(db,user,facility_id,kind):
    if not user.active:
        raise HTTPException(403,'Account is inactive')
    await require('reports.read')(user,db)
    await require('reports.export')(user,db)
    if kind=='transfers':
        global_only(user)
    if kind=='staff':
        await require('workforce.read')(user,db)
    await check_facility(db,user,facility_id)


async def request(db,user,payload,schedule=False):
    await authorize(db,user,payload.facility_id,payload.kind)
    if schedule:
        row=ReportSchedule(owner_id=user.id,**payload.model_dump(),next_run=datetime.now(timezone.utc))
    else:
        if getattr(payload,'idempotency_key',None):
            # Serialize this actor's keyed requests before checking the receipt.
            # The job and receipt commit together in the request transaction.
            await db.scalar(select(User).where(User.id==user.id).with_for_update())
            previous=await replay(db,user.id,'report.request',payload)
            if previous is not None:
                return previous
        row=ReportJob(owner_id=user.id,**payload.model_dump(exclude={'idempotency_key'}),expires_at=datetime.now(timezone.utc)+timedelta(days=1))
    db.add(row)
    await db.flush()
    audit(db,user.id,'report.scheduled' if schedule else 'report.requested',{'id':str(row.id)})
    result=serialize(row,('content',))
    return result if schedule else remember(db,user.id,'report.request',payload,result)


async def due_schedules(db):
    now=datetime.now(timezone.utc)
    rows=await db.scalars(select(ReportSchedule).where(ReportSchedule.active.is_(True),ReportSchedule.next_run<=now)
                          .order_by(ReportSchedule.next_run).limit(100).with_for_update(skip_locked=True))
    count=0
    for row in rows:
        db.add(ReportJob(owner_id=row.owner_id,facility_id=row.facility_id,kind=row.kind,format=row.format,expires_at=now+timedelta(days=1)))
        row.next_run=now+timedelta(minutes=row.interval_minutes)
        count+=1
    return count


async def generate_pending(db):
    row=await db.scalar(select(ReportJob).where(ReportJob.status=='pending').order_by(ReportJob.created_at).limit(1).with_for_update(skip_locked=True))
    if not row:
        return 0
    user=await get_record(db,User,row.owner_id)
    try:
        await authorize(db,user,row.facility_id,row.kind)
    except HTTPException:
        row.status,row.failure_code='failed','ACCESS_REVOKED'
        return 0
    result=await report(db,user,row.kind,0,500,facility_id=row.facility_id)
    if result['has_more']:
        row.status,row.failure_code='failed','REPORT_TOO_LARGE_USE_PAGINATED_EXPORT'
        return 0
    try:
        row.content,row.media_type=await run_in_threadpool(export,result['rows'],row.format)
    except Exception:
        row.status,row.failure_code='failed','EXPORT_GENERATION_FAILED'
        return 0
    row.status='completed'
    audit(db,user.id,'report.completed',{'id':str(row.id)})
    return 1

async def expire_artifacts(db,limit=100):
    rows=await db.scalars(select(ReportJob).where(ReportJob.expires_at<=datetime.now(timezone.utc),ReportJob.status!='expired')
                          .order_by(ReportJob.expires_at).limit(limit).with_for_update(skip_locked=True))
    count=0
    for row in rows:
        row.content=None
        row.status='expired'
        audit(db,row.owner_id,'report.expired',{'id':str(row.id)})
        count+=1
    return count
