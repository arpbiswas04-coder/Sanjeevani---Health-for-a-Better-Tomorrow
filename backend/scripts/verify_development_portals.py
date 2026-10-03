"""Local-only portal HTTP verification, with isolated labeled bed fixtures.

Uses the guarded development DB and ignored credentials. Never emits secrets.
"""
import asyncio
import json
from pathlib import Path
import httpx
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine
from app.models import User, Role, Permission, RolePermission, UserRole, Facility, BedCapacity
from app.security.scope import facility_filter
from scripts.development_data import guard, ROOT
from scripts.development_accounts import identity_snapshot
from scripts.development_portals import POLICIES


async def verify():
    api='http://127.0.0.1:8001'
    credentials=json.loads((ROOT/'tmp/development-data/credentials.json').read_text())
    credentials.update(json.loads((ROOT/'tmp/development-data/portal-credentials.json').read_text()))
    result={'api':api,'accounts':{}}
    async with AsyncSessionLocal() as db:
        await guard(db)
        protected=await identity_snapshot(db,'arpan')
        target=await db.scalar(select(Facility).where(Facility.code=='DEV-PHASE3'))
        outside=await db.scalar(select(Facility).where(Facility.code.like('FD1-%')).order_by(Facility.code))
        assert target and outside and target.block_id and outside.id!=target.id
        async with httpx.AsyncClient(base_url=api,timeout=30) as client:
            for level,credential in credentials.items():
                assert credential['username'].startswith('dev-')
                response=await client.post('/api/v1/auth/login',data=credential)
                assert response.status_code==200,(level,response.status_code)
                token=response.json()['access_token'];assert len(token.split('.'))==3
                client.headers['Authorization']='Bearer '+token
                response=await client.get('/api/v1/users/me');assert response.status_code==200
                me=response.json()['data']
                snapshot=await identity_snapshot(db,credential['username'])
                user=await db.scalar(select(User).where(User.username==credential['username']))
                roles=sorted(await db.scalars(select(Role.name).join(UserRole).where(UserRole.user_id==user.id)))
                assert me['id']==str(user.id) and sorted(me['roles'])==roles
                assert sorted(me['permissions'])==snapshot['permissions']
                assert sorted(me['facility_ids'])==snapshot['facilities'] and sorted(me['district_ids'])==snapshot['districts']
                assert me['scope_mode']==user.scope_mode
                expected=list(await db.scalars(select(Facility).where(Facility.active.is_(True),facility_filter(user,Facility.id))))
                response=await client.get('/api/v1/facilities',params={'limit':200});assert response.status_code==200
                assert {r['id'] for r in response.json()['data']}=={str(f.id) for f in expected}
                selected=target if level in POLICIES or level=='admin' else outside
                assert selected.id in {f.id for f in expected}
                response=await client.get('/api/v1/inventory',params={'facility_id':str(selected.id)})
                assert response.status_code==200
                admin=level=='admin'
                assert (await client.get('/api/v1/users')).status_code==(200 if admin else 403)
                denied={'read_admin':not admin}
                if not admin:
                    assert (await client.post('/api/v1/roles',json={'name':'SHOULD-NOT-EXIST-PORTAL'})).status_code==403
                    denied['admin_write']=True
                if user.scope_mode=='restricted':
                    excluded=next(f for f in await db.scalars(select(Facility)) if f.id not in {r.id for r in expected})
                    assert (await client.get('/api/v1/inventory',params={'facility_id':str(excluded.id)})).status_code==404
                    rejected={'facility_id':str(excluded.id),'bed_type':'DEV-PORTAL-DENIED','capacity':2,'occupied':1}
                    before=list(await db.scalars(select(BedCapacity.id).where(BedCapacity.bed_type=='DEV-PORTAL-DENIED')))
                    assert (await client.put('/api/v1/beds',json=rejected)).status_code==(404 if 'beds.write' in me['permissions'] else 403)
                    after=list(await db.scalars(select(BedCapacity.id).where(BedCapacity.bed_type=='DEV-PORTAL-DENIED')))
                    assert before==after
                    denied['outside_read_write']=True
                if level in POLICIES:
                    payload={'facility_id':str(target.id),'bed_type':'DEV-PORTAL-'+level,'capacity':2,'occupied':1}
                    response=await client.put('/api/v1/beds',json=payload);assert response.status_code==200
                    row=await db.scalar(select(BedCapacity).where(BedCapacity.facility_id==target.id,BedCapacity.bed_type==payload['bed_type']))
                    assert row and row.capacity==2 and row.occupied==1
                    refreshed=await client.get('/api/v1/operations/beds',params={'facility_id':str(target.id),'limit':200})
                    assert any(r['id']==str(row.id) and r['occupied']==1 for r in refreshed.json()['data'])
                result['accounts'][level]={'username':credential['username'],'role':roles[0], 'permissions':me['permissions'],
                    'scope_mode':me['scope_mode'],'facility_ids':me['facility_ids'],'district_ids':me['district_ids'],
                    'visible_facility_ids':sorted(str(f.id) for f in expected),'selected_facility_id':str(selected.id),
                    'selected_facility_name':selected.name,'denied':denied,'bed_mutation':level in POLICIES}
                assert (await client.post('/api/v1/auth/logout')).status_code==200
                assert (await client.get('/api/v1/users/me')).status_code==401
                assert (await client.put('/api/v1/beds',json={'facility_id':str(target.id),'bed_type':'DEV-PORTAL-DENIED','capacity':2,'occupied':1})).status_code==401
        assert await identity_snapshot(db,'arpan')==protected
        result['arpan_unchanged']=True
    await engine.dispose()
    return result


if __name__=='__main__':
    result=asyncio.run(verify())
    directory=ROOT/'tmp/portal-accounts';directory.mkdir(parents=True,exist_ok=True)
    (directory/'http.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'verified_accounts':len(result['accounts']),'arpan_unchanged':result['arpan_unchanged']}))
