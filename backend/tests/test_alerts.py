from datetime import datetime,timezone,timedelta
from uuid import UUID
import pytest
from sqlalchemy import select,func
from app.models import User
from app.models.alerts import Alert,NotificationLog,EscalationHistory
from app.services.alerts import evaluate_rule,escalate
from app.services.notifications import NotificationService
from tests.test_platform import seed,receipt
pytestmark=pytest.mark.asyncio


async def test_alert_dedup_escalation_delivery(api):
    client,factory,_=api
    ids=await seed(client)
    await client.post('/api/v1/inventory/receive',json=receipt(ids))
    rule=await client.post('/api/v1/alert-rules',json={'facility_id':ids['facility_id'],'kind':'LOW_STOCK','threshold':20,'severity':'critical'})
    assert rule.status_code==201
    rid=UUID(rule.json()['data']['id'])
    async with factory.begin() as db:
        assert await evaluate_rule(db,rid)==1
    async with factory.begin() as db:
        assert await evaluate_rule(db,rid)==0
        alert=await db.scalar(select(Alert))
        alert.created_at=datetime.now(timezone.utc)-timedelta(hours=1)
        admin=await db.scalar(select(User).where(User.username=='admin'))
        aid,uid=str(alert.id),str(admin.id)
    response=await client.post('/api/v1/escalation-rules',json={'rule_id':str(rid),'after_minutes':5,'recipient_id':uid})
    assert response.status_code==201
    async with factory.begin() as db:
        assert await escalate(db)==1
    async with factory.begin() as db:
        assert await escalate(db)==0
        assert await NotificationService.deliver_pending(db)==1
    async with factory.begin() as db:
        assert await NotificationService.deliver_pending(db)==0
        assert await db.scalar(select(func.count()).select_from(EscalationHistory))==1
    assert (await client.get('/api/v1/notifications')).json()['data'][0]['status']=='delivered'
    assert (await client.post(f'/api/v1/alerts/{aid}/actions',json={'status':'acknowledged'})).status_code==200
    assert (await client.post(f'/api/v1/alerts/{aid}/actions',json={'status':'resolved'})).status_code==200
    assert (await client.post(f'/api/v1/alerts/{aid}/actions',json={'status':'acknowledged'})).status_code==409


async def test_external_notification_not_faked(api):
    client,factory,_=api
    ids=await seed(client)
    async with factory.begin() as db:
        user=await db.scalar(select(User).where(User.username=='admin'))
        await NotificationService.send(db,channel='email',recipient=user,template='test',data={},facility_id=UUID(ids['facility_id']),dedup_key='test-mail')
    async with factory.begin() as db:
        assert await NotificationService.deliver_pending(db)==0
        row=await db.scalar(select(NotificationLog))
        assert row.status=='failed' and row.failure_reason=='PROVIDER_NOT_CONFIGURED'

async def test_other_alert_rules(api):
    client,factory,_=api
    ids=await seed(client)
    await client.put('/api/v1/beds',json={'facility_id':ids['facility_id'],'bed_type':'ICU','capacity':10,'occupied':9})
    await client.post('/api/v1/cold-chain/observations',json={'facility_id':ids['facility_id'],'observed_at':datetime.now(timezone.utc).isoformat(),
        'temperature':10,'minimum':2,'maximum':8,'source':'test','external_id':'reading-1'})
    for kind,threshold in [('HIGH_BED_OCCUPANCY',0.8),('STAFFING_SHORTAGE',1),('COLD_CHAIN_EXCURSION',0)]:
        response=await client.post('/api/v1/alert-rules',json={'facility_id':ids['facility_id'],'kind':kind,'threshold':threshold})
        async with factory.begin() as db:
            assert await evaluate_rule(db,UUID(response.json()['data']['id']))==1

async def test_escalation_configuration_can_be_disabled(api):
    client,_,_=api
    ids=await seed(client)
    uid=(await client.get('/api/v1/users/me')).json()['data']['id']
    rule=(await client.post('/api/v1/alert-rules',json={'facility_id':ids['facility_id'],'kind':'LOW_STOCK','threshold':10})).json()['data']['id']
    payload={'rule_id':rule,'after_minutes':5,'recipient_id':uid}
    created=await client.post('/api/v1/escalation-rules',json=payload)
    identifier=created.json()['data']['id']
    response=await client.put('/api/v1/escalation-rules/'+identifier,json={**payload,'active':False})
    assert response.status_code==200 and response.json()['data']['active'] is False
    assert (await client.get('/api/v1/escalation-rules')).json()['data'][0]['active'] is False
