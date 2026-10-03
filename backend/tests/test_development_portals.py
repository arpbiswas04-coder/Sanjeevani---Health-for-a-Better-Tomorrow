import os
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from httpx import ASGITransport, AsyncClient
from app.models import Country, State, District, Block, Facility, User, BedCapacity
from app.core.database import get_db
from app.main import app
from scripts.development_portals import POLICIES, provision, jurisdiction
from scripts.development_accounts import identity_snapshot
from tests.test_postgres import pg


async def exercise(client, factory):
    credentials = {level:{'username':f'dev-{level}-admin','password':'isolated-portal-password'} for level in POLICIES}
    async with factory.begin() as db:
        country = Country(code='PORTAL',name='Isolated test country'); db.add(country); await db.flush()
        states = [State(code=str(i),name=f'Isolated state {i}',country_id=country.id) for i in range(2)]
        db.add_all(states); await db.flush()
        districts = [District(code=str(i),name=f'Isolated district {i}',state_id=states[0 if i<2 else 1].id) for i in range(3)]
        db.add_all(districts); await db.flush()
        blocks = [Block(code=str(i),name=f'Isolated block {i}',district_id=d.id) for i,d in enumerate(districts)]
        db.add_all(blocks); await db.flush()
        facilities = [Facility(code=f'PORTAL-{i}',name=f'Isolated facility {i}',block_id=blocks[[0,0,1,2][i]].id) for i in range(4)]
        db.add_all(facilities); await db.flush()
        args = (states[0].id,districts[0].id,facilities[0].id)
        before = await identity_snapshot(db,'arpan')
        first = await provision(db,credentials,*args)
        assert all(a['created'] for a in first['accounts'])
        again = await provision(db,credentials,*args)
        assert not any(a['created'] for a in again['accounts'])
        assert before == await identity_snapshot(db,'arpan')
        wrong = {**credentials, 'national':{**credentials['national'],'password':'different-isolated-password'}}
        with pytest.raises(ValueError,match='never reset'):
            await provision(db,wrong,*args)
        with pytest.raises(ValueError,match='hierarchy'):
            await jurisdiction(db,states[1].id,districts[0].id,facilities[0].id)
    for level in POLICIES:
        response = await client.post('/api/v1/auth/login',data=credentials[level])
        assert response.status_code == 200
        client.headers['Authorization']='Bearer '+response.json()['access_token']
        me=(await client.get('/api/v1/users/me')).json()['data']
        assert me['roles']==[level+'_admin'] and set(me['permissions'])==POLICIES[level]
        assert me['scope_mode']==('global' if level=='national' else 'restricted')
        expected = facilities if level=='national' else facilities[:3] if level=='state' else facilities[:2] if level=='district' else facilities[:1]
        rows=(await client.get('/api/v1/facilities',params={'limit':200})).json()['data']
        assert {r['id'] for r in rows if r['code'].startswith('PORTAL-')}=={str(f.id) for f in expected}
        assert (await client.get('/api/v1/users')).status_code==403
        for f in facilities:
            wanted = 200 if f in expected else 404
            assert (await client.get('/api/v1/inventory',params={'facility_id':str(f.id)})).status_code==wanted
            payload={'facility_id':str(f.id),'bed_type':'PORTAL-'+level,'capacity':2,'occupied':1}
            assert (await client.put('/api/v1/beds',json=payload)).status_code==wanted
            async with factory() as db:
                count=await db.scalar(select(func.count()).select_from(BedCapacity).where(BedCapacity.facility_id==f.id,BedCapacity.bed_type=='PORTAL-'+level))
                assert count==(1 if wanted==200 else 0)
        assert (await client.post('/api/v1/auth/logout')).status_code==200
        assert (await client.get('/api/v1/users/me')).status_code==401


@pytest.mark.asyncio
async def test_portal_policies_scope_reads_writes_and_replay(api):
    client,factory,_=api
    await exercise(client,factory)


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'),reason='Disposable PostgreSQL/PostGIS TEST_DATABASE_URL required')
async def test_portal_policies_postgres_http_scope_isolation(pg):
    factory,_,_,_=pg
    async def database():
        async with factory() as db:
            async with db.begin():yield db
    app.dependency_overrides[get_db]=database
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
            await exercise(client,factory)
    finally:
        app.dependency_overrides.pop(get_db,None)
