from datetime import datetime,timezone,timedelta
from hashlib import sha256
from sqlalchemy import select,func,case,and_,union
from fastapi import HTTPException
from app.models import Facility,Inventory,MedicineBatch,User
from app.models.operations import BedCapacity,Shift,Staff,TemperatureObservation
from app.models.stock import StockPolicy
from app.services.stock import expiry_cutoff
from app.models.alerts import AlertRule,Alert,EscalationRule,EscalationHistory
from app.repositories.common import get_record,serialize
from app.security.scope import check_facility
from app.services.inventory import audit
from app.services.notifications import NotificationService
from app.services.identity import aware


async def save_rule(db,user,payload,identifier=None):
    await check_facility(db,user,payload.facility_id)
    row=await get_record(db,AlertRule,identifier,lock=True) if identifier else AlertRule()
    if identifier:
        await check_facility(db,user,row.facility_id)
    for key,value in payload.model_dump().items():
        setattr(row,key,value)
    db.add(row)
    await db.flush()
    audit(db,user.id,'alert_rule.saved',{'id':str(row.id)})
    return serialize(row)


async def emit(db,rule,source,details):
    key=sha256(f'{rule.id}:{source}'.encode()).hexdigest()
    if not await db.scalar(select(Alert.id).where(Alert.active_key==key)):
        db.add(Alert(rule_id=rule.id,facility_id=rule.facility_id,kind=rule.kind,severity=rule.severity,
                     source=str(source),active_key=key,details=details))
        return 1
    return 0


async def evaluate_rule(db,identifier):
    rule=await get_record(db,AlertRule,identifier,lock=True)
    if not rule.active:
        return 0
    now=datetime.now(timezone.utc)
    query=None
    if rule.kind in ('LOW_STOCK','CRITICAL_STOCK'):
        usable=case((MedicineBatch.recalled.is_(False) & (MedicineBatch.expires_on>now.date()), Inventory.quantity-Inventory.reserved), else_=0)
        balances=select(MedicineBatch.medicine_id.label('medicine_id'),func.sum(usable).label('value')).join(Inventory).where(
            Inventory.facility_id==rule.facility_id).group_by(MedicineBatch.medicine_id).subquery()
        medicines=union(select(balances.c.medicine_id),select(StockPolicy.medicine_id).where(StockPolicy.facility_id==rule.facility_id)).subquery()
        value=func.coalesce(balances.c.value,0)
        query=select(medicines.c.medicine_id,value).outerjoin(balances,balances.c.medicine_id==medicines.c.medicine_id).where(value<=rule.threshold)
    elif rule.kind=='EXPIRY':
        query=select(Inventory.id,Inventory.quantity).join(MedicineBatch).outerjoin(StockPolicy,and_(
            StockPolicy.facility_id==Inventory.facility_id,StockPolicy.medicine_id==MedicineBatch.medicine_id)).where(
            Inventory.facility_id==rule.facility_id,Inventory.quantity>0,
            MedicineBatch.expires_on<=expiry_cutoff(db,func.coalesce(StockPolicy.expiry_warning_days,rule.window_days)))
    elif rule.kind=='HIGH_BED_OCCUPANCY':
        query=select(BedCapacity.id,BedCapacity.occupied).where(BedCapacity.facility_id==rule.facility_id,BedCapacity.capacity>0,
            BedCapacity.occupied>=BedCapacity.capacity*rule.threshold)
    elif rule.kind=='STAFFING_SHORTAGE':
        count=await db.scalar(select(func.count(func.distinct(Shift.staff_id))).join(Staff).where(Shift.facility_id==rule.facility_id,
            Shift.cancelled.is_(False),Staff.active.is_(True),Shift.starts_at<=now,Shift.ends_at>now))
        return await emit(db,rule,'current-shift',{'scheduled_staff':count,'minimum':rule.threshold}) if count<rule.threshold else 0
    elif rule.kind=='COLD_CHAIN_EXCURSION':
        query=select(TemperatureObservation.id,TemperatureObservation.temperature).where(TemperatureObservation.facility_id==rule.facility_id,
            TemperatureObservation.excursion.is_(True),TemperatureObservation.observed_at>=now-timedelta(days=rule.window_days))
    elif rule.kind=='MAINTENANCE':
        from app.models.assets import Equipment
        query=select(Equipment.id,Equipment.code).where(Equipment.facility_id==rule.facility_id,Equipment.next_maintenance<=now.date()+timedelta(days=rule.window_days))
    if query is None:
        return 0
    count=0
    # Stream the query rather than loading unbounded operational records.
    rows=await db.stream(query.execution_options(yield_per=200))
    async for source,value in rows:
        count+=await emit(db,rule,str(source),{'value':value,'threshold':rule.threshold})
    await db.flush()
    return count


async def change_status(db,user,identifier,payload):
    row=await get_record(db,Alert,identifier,lock=True)
    await check_facility(db,user,row.facility_id)
    if row.status=='resolved' or (row.status=='acknowledged' and payload.status=='acknowledged'):
        raise HTTPException(409,'Invalid alert transition')
    row.status=payload.status
    if row.status=='acknowledged':
        row.acknowledged_at=datetime.now(timezone.utc)
    else:
        row.resolved_at=datetime.now(timezone.utc)
        row.active_key=None
    audit(db,user.id,'alert.'+row.status,{'id':str(row.id)})
    await db.flush()
    return serialize(row)


async def escalation_create(db,user,payload):
    rule=await get_record(db,AlertRule,payload.rule_id)
    await check_facility(db,user,rule.facility_id)
    recipient=await get_record(db,User,payload.recipient_id)
    await check_facility(db,recipient,rule.facility_id)
    row=EscalationRule(**payload.model_dump())
    db.add(row)
    await db.flush()
    audit(db,user.id,'escalation.configured',{'id':str(row.id)})
    return serialize(row)


async def escalate(db,limit=100):
    now=datetime.now(timezone.utc)
    if db.bind.dialect.name=='postgresql':
        age=func.extract('epoch',now-Alert.created_at)
    else:
        age=(func.julianday(now)-func.julianday(Alert.created_at))*86400
    processed=select(EscalationHistory.id).where(EscalationHistory.alert_id==Alert.id,
        EscalationHistory.escalation_rule_id==EscalationRule.id).exists()
    rows=await db.execute(select(Alert,EscalationRule).join(EscalationRule,EscalationRule.rule_id==Alert.rule_id).where(
        Alert.status=='open',EscalationRule.active.is_(True),age>=EscalationRule.after_minutes*60,~processed)
        .order_by(Alert.created_at,EscalationRule.id).limit(limit).with_for_update(of=Alert,skip_locked=True))
    count=0
    for alert,rule in rows:
        recipient=await get_record(db,User,rule.recipient_id)
        if not recipient.active:
            continue
        try:
            await check_facility(db,recipient,alert.facility_id)
        except HTTPException:
            continue
        notification=await NotificationService.send(db,channel=rule.channel,recipient=recipient,template='alert_escalation',
            data={'alert_id':str(alert.id),'kind':alert.kind},facility_id=alert.facility_id,dedup_key=f'escalation:{alert.id}:{rule.id}')
        db.add(EscalationHistory(alert_id=alert.id,escalation_rule_id=rule.id,notification_id=notification.id))
        count+=1
    return count

async def escalation_update(db,user,identifier,payload):
    row=await get_record(db,EscalationRule,identifier,lock=True)
    previous=await get_record(db,AlertRule,row.rule_id)
    await check_facility(db,user,previous.facility_id)
    rule=await get_record(db,AlertRule,payload.rule_id)
    await check_facility(db,user,rule.facility_id)
    recipient=await get_record(db,User,payload.recipient_id)
    await check_facility(db,recipient,rule.facility_id)
    if row.rule_id!=payload.rule_id:
        raise HTTPException(409,'Create a new escalation rule to change the alert-rule association')
    for key,value in payload.model_dump().items():
        setattr(row,key,value)
    audit(db,user.id,'escalation.updated',{'id':str(row.id)})
    await db.flush()
    return serialize(row)
