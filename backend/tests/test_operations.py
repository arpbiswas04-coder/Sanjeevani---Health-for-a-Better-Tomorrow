from datetime import datetime,timezone,timedelta
import pytest
from tests.test_platform import seed
pytestmark=pytest.mark.asyncio


async def test_beds_cold_chain(api):
    client,_,_=api
    ids=await seed(client)
    bed={'facility_id':ids['facility_id'],'bed_type':'ICU','capacity':10,'occupied':9}
    first=await client.put('/api/v1/beds',json=bed)
    assert first.status_code==200
    assert first.json()['data']['available']==1
    assert (await client.put('/api/v1/beds',json={**bed,'occupied':11})).status_code==422
    await client.put('/api/v1/beds',json={**bed,'occupied':8})
    assert len((await client.get('/api/v1/beds/'+first.json()['data']['id']+'/history')).json()['data'])==2
    observation={'facility_id':ids['facility_id'],'observed_at':datetime.now(timezone.utc).isoformat(),
                 'temperature':12,'minimum':2,'maximum':8,'source':'test-sensor','external_id':'event-1'}
    response=await client.post('/api/v1/cold-chain/observations',json=observation)
    assert response.status_code==201 and response.json()['data']['excursion']
    assert (await client.post('/api/v1/cold-chain/observations',json=observation)).json()==response.json()
    assert (await client.post('/api/v1/cold-chain/observations',json={**observation,'temperature':4})).status_code==409


async def test_workforce_and_aggregates(api):
    client,_,_=api
    ids=await seed(client)
    role=(await client.post('/api/v1/staff-roles',json={'name':'Nurse'})).json()['data']['id']
    staff=await client.post('/api/v1/staff',json={'facility_id':ids['facility_id'],'staff_role_id':role,'code':'S1','display_name':'Staff One'})
    assert staff.status_code==201
    sid=staff.json()['data']['id']
    now=datetime.now(timezone.utc)
    shift={'staff_id':sid,'starts_at':now.isoformat(),'ends_at':(now+timedelta(hours=8)).isoformat()}
    assert (await client.post('/api/v1/shifts',json=shift)).status_code==201
    assert (await client.post('/api/v1/shifts',json=shift)).status_code==409
    attendance={'staff_id':sid,'day':str(now.date()),'status':'present'}
    assert (await client.post('/api/v1/attendance',json=attendance)).status_code==201
    assert (await client.post('/api/v1/attendance',json=attendance)).status_code==409
    aggregate={'facility_id':ids['facility_id'],'day':str(now.date()),'category':'outpatient','count':20}
    assert (await client.put('/api/v1/aggregates/footfall',json=aggregate)).status_code==200
    assert (await client.put('/api/v1/aggregates/footfall',json=aggregate)).status_code==409
    assert (await client.put('/api/v1/aggregates/footfall',json={**aggregate,'expected_version':1,'count':25})).json()['data']['version']==2
