from datetime import date,timedelta
from app.core.time import utc_today
from uuid import UUID
import pytest
from app.services.alerts import evaluate_rule
from tests.test_platform import seed
pytestmark=pytest.mark.asyncio


async def test_assets_maintenance_and_alert(api):
    client,factory,_=api
    ids=await seed(client)
    row=await client.post('/api/v1/equipment',json={'facility_id':ids['facility_id'],'code':'EQ1','equipment_type':'ventilator','next_maintenance':str(utc_today())})
    assert row.status_code==201
    eid=row.json()['data']['id']
    rule=(await client.post('/api/v1/alert-rules',json={'facility_id':ids['facility_id'],'kind':'MAINTENANCE','threshold':0})).json()['data']['id']
    async with factory.begin() as db:
        assert await evaluate_rule(db,UUID(rule))==1
    maintained=await client.post(f'/api/v1/equipment/{eid}/maintenance',json={'performed_on':str(utc_today()),'next_due':str(utc_today()+timedelta(days=180)),'notes':'Serviced'})
    assert maintained.status_code==201
    assert len((await client.get(f'/api/v1/equipment/{eid}/maintenance')).json()['data'])==1
    assert (await client.post('/api/v1/ambulances',json={'facility_id':ids['facility_id'],'vehicle_id':'AMB1'})).status_code==201
    assert (await client.post('/api/v1/ambulances',json={'facility_id':ids['facility_id'],'vehicle_id':'AMB2','operational':False})).status_code==422


async def test_equipment_update_availability_maintenance_dates(api):
    client,_,_=api
    ids=await seed(client)
    payload={'facility_id':ids['facility_id'],'code':'DIRECT-EQ','equipment_type':'oxygen concentrator','status':'available'}
    created=await client.post('/api/v1/equipment',json=payload)
    assert created.status_code==201
    identifier=created.json()['data']['id']
    for status in ('in_use','maintenance','available'):
        response=await client.put('/api/v1/equipment/'+identifier,json={**payload,'status':status})
        assert response.status_code==200 and response.json()['data']['status']==status
        records=(await client.get('/api/v1/assets/equipment',params={'facility_id':ids['facility_id']})).json()['data']
        assert records[0]['status']==status
    assert (await client.put('/api/v1/equipment/'+identifier,json={**payload,'status':'unknown'})).status_code==422
    tomorrow=utc_today()+timedelta(days=1)
    body={'performed_on':str(tomorrow),'next_due':str(tomorrow+timedelta(days=30)),'notes':'Future'}
    assert (await client.post('/api/v1/equipment/'+identifier+'/maintenance',json=body)).status_code==422
    body['performed_on']=str(utc_today())
    assert (await client.post('/api/v1/equipment/'+identifier+'/maintenance',json=body)).status_code==201
    history=(await client.get('/api/v1/equipment/'+identifier+'/maintenance')).json()['data']
    assert len(history)==1 and history[0]['performed_on']==str(utc_today())


async def test_ambulance_creation_update_and_availability(api):
    client,_,_=api
    ids=await seed(client)
    payload={'facility_id':ids['facility_id'],'vehicle_id':'DIRECT-AMB','status':'available','operational':True}
    response=await client.post('/api/v1/ambulances',json=payload)
    assert response.status_code==201
    identifier=response.json()['data']['id']
    for status,operational in [('assigned',True),('in_transit',True),('maintenance',False),('available',True)]:
        update=await client.put('/api/v1/ambulances/'+identifier,json={**payload,'status':status,'operational':operational})
        assert update.status_code==200 and update.json()['data']['status']==status
    records=(await client.get('/api/v1/assets/ambulances',params={'facility_id':ids['facility_id']})).json()['data']
    assert records[0]['operational'] is True and records[0]['status']=='available'
    assert (await client.put('/api/v1/ambulances/'+identifier,json={**payload,'operational':False})).status_code==422
    assert (await client.put('/api/v1/ambulances/'+identifier,json={**payload,'latitude':20})).status_code==422


async def test_asset_facility_scope_and_permissions(api):
    from tests.test_operations_permissions import grant
    from app.security.auth import access_token
    client,factory,reader=api
    ids=await seed(client)
    other=(await client.post('/api/v1/facilities',json={'name':'Other','code':'ASSET-OTHER'})).json()['data']['id']
    equipment={'facility_id':other,'code':'PRIVATE-EQ','equipment_type':'ventilator'}
    ambulance={'facility_id':other,'vehicle_id':'PRIVATE-AMB'}
    eid=(await client.post('/api/v1/equipment',json=equipment)).json()['data']['id']
    aid=(await client.post('/api/v1/ambulances',json=ambulance)).json()['data']['id']
    client.headers['Authorization']='Bearer '+access_token(reader)
    assert (await client.post('/api/v1/equipment',json=equipment)).status_code==403
    assert (await client.post('/api/v1/ambulances',json=ambulance)).status_code==403
    await grant(factory,reader,ids['facility_id'],['equipment.read','equipment.write'])
    for kind in ('equipment','ambulances'):
        assert (await client.get('/api/v1/assets/'+kind,params={'facility_id':ids['facility_id']})).status_code==200
        assert (await client.get('/api/v1/assets/'+kind,params={'facility_id':other})).status_code==404
    assert (await client.put('/api/v1/equipment/'+eid,json=equipment)).status_code==404
    assert (await client.put('/api/v1/ambulances/'+aid,json=ambulance)).status_code==404
    assert (await client.get('/api/v1/equipment/'+eid+'/maintenance')).status_code==404
    assert (await client.post('/api/v1/equipment/'+eid+'/maintenance',json={'performed_on':str(utc_today()),'next_due':str(utc_today()+timedelta(days=30)),'notes':'Forbidden'})).status_code==404
