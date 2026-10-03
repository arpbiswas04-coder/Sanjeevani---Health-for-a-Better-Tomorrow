"""Explicit local HTTP/SQL verification. Never prints credentials or JWTs.

From backend: python -m scripts.verify_functional_completion --api http://127.0.0.1:8001
Requires the private development credentials created during local setup.
"""
import argparse
import asyncio
from hashlib import sha256
from datetime import date,datetime,time,timezone,timedelta
import json
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID
import httpx
from sqlalchemy import select,func,text
from app.core.database import AsyncSessionLocal,engine
from app.models import (User,UserRole,UserFacility,Facility,Medicine,Inventory,StockTransaction,
    BedCapacity,Staff,Shift,Attendance,Equipment,Ambulance,PatientFootfall,Alert,Shipment,
    Supplier,Warehouse,PurchaseOrder,TransferRequest,Country,State,District,Block,AuditLog,MutationReceipt,MedicineBatch)
from scripts.development_data import guard
from scripts.development_seed import PROFILES
from scripts.development_accounts import identity_snapshot

ROOT=Path(__file__).resolve().parents[2]


async def verify(api,credentials_file,seed):
    url=urlparse(api)
    if url.hostname not in ('localhost','127.0.0.1') or url.scheme!='http':raise ValueError('Local development HTTP only')
    credentials=json.loads(credentials_file.read_text())
    result={'api':api,'checks':{},'profiles':{}}
    async with AsyncSessionLocal() as db:
        await guard(db)
        async def signature():
            user=await db.scalar(select(User).where(User.username=='arpan'))
            if not user:return None
            roles=sorted(str(v) for v in await db.scalars(select(UserRole.role_id).where(UserRole.user_id==user.id)))
            return sha256(json.dumps([str(user.id),user.password_hash,user.active,user.token_version,user.scope_mode,roles]).encode()).hexdigest()
        original=await signature()
        protected_identity=await identity_snapshot(db,'arpan')
        receipt=await db.scalar(select(MutationReceipt).where(MutationReceipt.operation=='devdata.operations',MutationReceipt.key==str(seed)))
        if not receipt:raise ValueError('Owned base seed required')
        facility_ids=[UUID(v) for v in receipt.response['facility_ids']]
        selected=facility_ids[0]
        async with httpx.AsyncClient(base_url=api,timeout=30) as client:
            schema=(await client.get('/api/v1/openapi.json')).json()
            assert 'location_context' in schema['components']['schemas']['FacilityView']['properties']
            result['openapi_operations']=sum(len(set(v)&{'get','post','put','patch','delete'}) for v in schema['paths'].values())
            async def data(path,params=None):
                response=await client.get('/api/v1'+path,params=params)
                assert response.status_code==200,(path,response.status_code)
                return response.json()['data']
            async def listing(path,params=None):
                rows=[]
                for offset in range(0,20000,200):
                    page=await data(path,{**(params or {}),'offset':offset,'limit':200});rows+=page
                    if len(page)<200:return rows
                raise AssertionError('Unexpected directory size')
            for profile in ('admin','operator','inventory','reader'):
                cred=credentials[profile]
                assert cred['username']=='dev-data-'+profile
                response=await client.post('/api/v1/auth/login',data=cred)
                assert response.status_code==200,(profile,response.status_code)
                token=response.json()['access_token'];assert len(token.split('.'))==3
                client.headers['Authorization']='Bearer '+token
                me=await data('/users/me');user=await db.scalar(select(User).where(User.username==cred['username']))
                scopes=sorted(str(v) for v in await db.scalars(select(UserFacility.facility_id).where(UserFacility.user_id==user.id)))
                assert me['id']==str(user.id) and me['roles']==[PROFILES[profile][0]]
                assert set(me['permissions'])==PROFILES[profile][1] and sorted(me['facility_ids'])==scopes
                assert me['scope_mode']==user.scope_mode and me['district_ids']==[]
                facilities=await listing('/facilities');expected=list(await db.scalars(select(Facility).where(Facility.active.is_(True))))
                if profile!='admin':expected=[r for r in expected if str(r.id) in scopes]
                assert {r['id'] for r in facilities}=={str(r.id) for r in expected}
                if profile=='admin':
                    annotated=[r for r in facilities if r.get('location_context')]
                    assert annotated and all(r['latitude'] is None and r['longitude'] is None for r in annotated)
                    result['map']={'total':len(facilities),'recorded_points':sum(r['latitude'] is not None and r['longitude'] is not None for r in facilities),
                        'approximate_points':len(annotated)}
                    result['map']['unlocated']=len(facilities)-result['map']['recorded_points']-len(annotated)
                    for path,model in [('/medicines',Medicine),('/suppliers',Supplier),('/warehouses',Warehouse),('/purchase-orders',PurchaseOrder),
                            ('/transfers',TransferRequest),('/shipments',Shipment),('/alerts',Alert),('/geography/countries',Country),
                            ('/geography/states',State),('/geography/districts',District),('/geography/blocks',Block)]:
                        actual=await listing(path);records=list(await db.scalars(select(model)))
                        assert {r['id'] for r in actual}=={str(r.id) for r in records},path
                        result['checks'][path]=len(actual)
                    for point in annotated:
                        detail=await data('/facilities/'+point['id']);assert detail['location_context']==point['location_context']
                    for identifier in facility_ids:
                        for kind,model in [('beds',BedCapacity),('staff',Staff),('shifts',Shift),('attendance',Attendance),
                                ('footfall',PatientFootfall),('equipment',Equipment),('ambulances',Ambulance)]:
                            path=('/assets/' if kind in ('equipment','ambulances') else '/operations/')+kind
                            rows=await listing(path,{'facility_id':str(identifier)})
                            records=list(await db.scalars(select(model).where(model.facility_id==identifier)))
                            assert {r['id'] for r in rows}=={str(r.id) for r in records} and rows
                    for kind in ('stock','beds','staff','procurement','expiry'):
                        report=await data('/reports/'+kind,{'facility_id':str(selected),'limit':100})
                        assert report['rows'],kind
                        result['checks']['/reports/'+kind]=len(report['rows'])
                    temperatures=await listing('/operations/temperatures',{'facility_id':str(selected)})
                    assert any(r['excursion'] and 'SYNTHETIC' in r['source'] for r in temperatures)
                    result['checks']['/operations/temperatures']=len(temperatures)
                    day=date.fromisoformat(receipt.response['as_of']);start=datetime.combine(day,time.min,tzinfo=timezone.utc)
                    medicine_id=UUID(receipt.response['medicine_ids'][0])
                    quantity=await db.scalar(select(-func.sum(StockTransaction.quantity)).join(Inventory).join(MedicineBatch).where(
                        Inventory.facility_id==selected,MedicineBatch.medicine_id==medicine_id,StockTransaction.kind=='issue',
                        StockTransaction.created_at>=start,StockTransaction.created_at<start+timedelta(days=1)))
                    consumption=await data('/datasets/medicine-consumption',{'facility_id':str(selected),'medicine_id':str(medicine_id),
                        'start_date':str(day),'end_date':str(day)})
                    assert consumption==[{'day':str(day),'consumed':quantity}]
                    result['consumption']={'day':str(day),'medicine_id':str(medicine_id),'consumed':quantity}
                    result['checks']['/datasets/medicine-consumption']='HTTP rows match UTC ledger sum'
                stocks=await listing('/inventory',{'facility_id':str(selected)})
                records=list(await db.scalars(select(Inventory).where(Inventory.facility_id==selected)))
                assert {r['id'] for r in stocks}=={str(r.id) for r in records}
                by_id={str(r.id):r for r in records}
                for row in stocks:
                    assert row['quantity']==by_id[row['id']].quantity
                    assert row['quantity']==await db.scalar(select(func.sum(StockTransaction.quantity)).where(StockTransaction.inventory_id==by_id[row['id']].id))
                assert (await client.get('/api/v1/users')).status_code==(200 if profile=='admin' else 403)
                if profile!='admin':
                    outside=await db.scalar(select(Facility.id).where(Facility.id.not_in([UUID(v) for v in scopes])).limit(1))
                    assert outside is not None
                    assert (await client.get('/api/v1/inventory',params={'facility_id':str(outside)})).status_code==404
                if profile=='inventory':
                    assert (await client.get('/api/v1/operations/staff',params={'facility_id':str(selected)})).status_code==403
                if profile=='reader':
                    assert (await client.put('/api/v1/beds',json={'facility_id':str(selected),'bed_type':'DENIED','capacity':1,'occupied':0})).status_code==403
                    assert (await client.get('/api/v1/inventory',params={'facility_id':receipt.response['depot_id']})).status_code==404
                result['profiles'][profile]={'username':cred['username'],'role':me['roles'][0],'permissions':sorted(me['permissions']),
                    'scope_mode':me['scope_mode'],'facility_ids':scopes,'visible_facilities':len(facilities),'inventory_records':len(stocks),
                    'map_count':sum((r['latitude'] is not None and r['longitude'] is not None) or bool(r.get('location_context')) for r in facilities)}
                assert (await client.post('/api/v1/auth/logout')).status_code==200
                assert (await client.get('/api/v1/users/me')).status_code==401
        result['arpan_unchanged']=original==await signature();assert result['arpan_unchanged']
        result['arpan_complete_identity_unchanged']=protected_identity==await identity_snapshot(db,'arpan')
        assert result['arpan_complete_identity_unchanged']
        baseline=ROOT/'tmp/development-data/before.json'
        if baseline.exists():
            result['arpan_original_baseline_match']=original==json.loads(baseline.read_text())['arpan_signature'];assert result['arpan_original_baseline_match']
        facility=await db.get(Facility,selected)
        result['selected_facility']={'id':str(selected),'name':facility.name}
        bed=await db.scalar(select(BedCapacity).where(BedCapacity.facility_id==selected))
        result['bed']={'capacity':bed.capacity,'occupied':bed.occupied,'bed_type':bed.bed_type}
        result['staff_code']=await db.scalar(select(Staff.code).where(Staff.facility_id==selected))
        result['supplier_name']=await db.scalar(select(Supplier.name).where(Supplier.code==f'DEVOPS-{seed}-SUP'))
        result['annotated_names']=[r['name'] for r in annotated]
    await engine.dispose()
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api',default='http://127.0.0.1:8001')
    parser.add_argument('--credentials-file',type=Path,default=ROOT/'tmp/development-data/credentials.json')
    parser.add_argument('--seed',type=int,default=20261003)
    args=parser.parse_args()
    result=asyncio.run(verify(args.api,args.credentials_file,args.seed))
    folder=ROOT/'tmp/functional-completion';folder.mkdir(parents=True,exist_ok=True)
    (folder/'http-verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
