from app.schemas import outputs as out
from uuid import UUID
from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.models.alerts import Alert,AlertRule,NotificationLog
from app.schemas.alerts import RuleInput,AlertAction,EscalationInput
from app.security.auth import require,current_user
from app.security.scope import check_facility,facility_filter
from app.repositories.common import get_record,serialize
from app.services import alerts

router=APIRouter(responses=out.ERROR_RESPONSES, tags=['Alerts and notifications'])


@router.post('/alert-rules',status_code=201, response_model=out.Success[out.AlertRuleView], response_model_exclude_unset=True)
async def create_rule(payload:RuleInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('admin.config'))):
    return {'success':True,'data':await alerts.save_rule(db,user,payload)}


@router.put('/alert-rules/{identifier}', response_model=out.Success[out.AlertRuleView], response_model_exclude_unset=True)
async def update_rule(identifier:UUID,payload:RuleInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('admin.config'))):
    return {'success':True,'data':await alerts.save_rule(db,user,payload,identifier)}


@router.get('/alert-rules', response_model=out.Success[list[out.AlertRuleView]], response_model_exclude_unset=True)
async def rules(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('alerts.read'))):
    rows=await db.scalars(select(AlertRule).where(facility_filter(user,AlertRule.facility_id)).order_by(AlertRule.id).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(r) for r in rows]}


@router.post('/alert-rules/{identifier}/evaluate',status_code=202, response_model=out.Success[out.TaskQueued], response_model_exclude_unset=True)
async def evaluate(identifier:UUID,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('alerts.manage'))):
    rule=await get_record(db,AlertRule,identifier)
    await check_facility(db,user,rule.facility_id)
    from app.tasks.jobs import evaluate as job
    try:
        result=job.apply_async(args=[str(identifier)],retry=False)
    except Exception:
        raise HTTPException(503,'Background queue unavailable')
    return {'success':True,'data':{'task_id':result.id}}


@router.get('/alerts', response_model=out.Success[list[out.AlertView]], response_model_exclude_unset=True)
async def listing(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('alerts.read'))):
    rows=await db.scalars(select(Alert).where(facility_filter(user,Alert.facility_id)).order_by(Alert.created_at,Alert.id).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(r) for r in rows]}


@router.post('/alerts/{identifier}/actions', response_model=out.Success[out.AlertView], response_model_exclude_unset=True)
async def action(identifier:UUID,payload:AlertAction,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('alerts.manage'))):
    return {'success':True,'data':await alerts.change_status(db,user,identifier,payload)}


@router.post('/escalation-rules',status_code=201, response_model=out.Success[out.EscalationRuleView], response_model_exclude_unset=True)
async def escalation(payload:EscalationInput,db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(require('admin.config'))):
    return {'success':True,'data':await alerts.escalation_create(db,user,payload)}


@router.get('/notifications', response_model=out.Success[list[out.NotificationLogView]], response_model_exclude_unset=True)
async def notifications(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db, scope="function"),user:User=Depends(current_user)):
    rows=await db.scalars(select(NotificationLog).where(NotificationLog.recipient_id==user.id,
        facility_filter(user,NotificationLog.facility_id)).order_by(NotificationLog.created_at).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(r) for r in rows]}

@router.post('/notifications/{identifier}/retry', response_model=out.Success[out.RetryResult], response_model_exclude_unset=True)
async def retry_notification(identifier:UUID,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('alerts.manage'))):
    from app.services.inventory import audit
    row=await get_record(db,NotificationLog,identifier,lock=True)
    await check_facility(db,user,row.facility_id)
    if row.status!='failed':
        raise HTTPException(409,'Only failed notifications can be retried')
    row.status,row.attempts,row.failure_reason='pending',0,None
    audit(db,user.id,'notification.retry',{'id':str(row.id)})
    return {'success':True,'data':{'id':row.id,'status':row.status}}

@router.get('/escalation-rules', response_model=out.Success[list[out.EscalationRuleView]], response_model_exclude_unset=True)
async def escalation_rules(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('alerts.read'))):
    from app.models.alerts import EscalationRule
    rows=await db.scalars(select(EscalationRule).join(AlertRule).where(facility_filter(user,AlertRule.facility_id))
                          .order_by(EscalationRule.id).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(row) for row in rows]}


@router.put('/escalation-rules/{identifier}', response_model=out.Success[out.EscalationRuleView], response_model_exclude_unset=True)
async def escalation_update(identifier:UUID,payload:EscalationInput,db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('admin.config'))):
    return {'success':True,'data':await alerts.escalation_update(db,user,identifier,payload)}


@router.get('/alerts/{identifier}/escalations', response_model=out.Success[list[out.EscalationHistoryView]], response_model_exclude_unset=True)
async def escalation_history(identifier:UUID,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),db:AsyncSession=Depends(get_db,scope='function'),user:User=Depends(require('alerts.read'))):
    from app.models.alerts import EscalationHistory
    alert=await get_record(db,Alert,identifier)
    await check_facility(db,user,alert.facility_id)
    rows=await db.scalars(select(EscalationHistory).where(EscalationHistory.alert_id==identifier)
                          .order_by(EscalationHistory.created_at,EscalationHistory.id).offset(offset).limit(limit))
    return {'success':True,'data':[serialize(row) for row in rows]}
