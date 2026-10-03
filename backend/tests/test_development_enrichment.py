"""No persistent development writes: exercise annotations and enrichment in isolation."""
import json
from uuid import UUID
import pytest
from sqlalchemy import select,func
from app.core.database import Base
from app.models import (Facility,Medicine,User,AuditLog,Inventory,StockTransaction,
                        Ambulance,MaintenanceRecord,Shipment,PurchaseOrder)
from app.services.inventory import audit
from scripts.development_seed import create_user,seed_operations
from scripts.development_enrichment import annotate_locations,enrich,REFERENCES


@pytest.mark.asyncio
async def test_location_annotations_are_scoped_approximate_and_never_exact(api):
    client,factory,reader_id=api
    ref=json.loads(REFERENCES.read_text());point=ref['cities'][0]
    async with factory.begin() as db:
        owner=await db.scalar(select(User).where(User.username=='admin'))
        f=Facility(code='FD1-location',name='Source facility',address=f"{point['city']}; PIN 000000; {point['state']}")
        db.add(f);await db.flush()
        audit(db,owner.id,'devdata.facilities.imported',{'id':str(f.id),'code':f.code,'city':point['city'],
            'state':point['state'],'pincode':'000000','source_sha256':'source-row'})
        await db.flush()
        assert await annotate_locations(db,owner,ref)==1
        assert await annotate_locations(db,owner,ref)==0
        assert f.latitude is None and f.longitude is None and f.block_id is None
    r=await client.get('/api/v1/facilities');assert r.status_code==200
    row=r.json()['data'][0];assert row['location_context']['precision']=='approximate_city'
    assert row['latitude'] is None and row['longitude'] is None
    nearby=await client.get('/api/v1/facilities/nearby',params={'latitude':point['latitude'],'longitude':point['longitude'],'radius_km':1})
    assert nearby.json()['data']==[]
    async with factory.begin() as db:
        await create_user(db,'reader','isolated-location-password',[f.id])
        second=Facility(code='FD1-other',name='Outside scope');db.add(second);await db.flush()
    login=await client.post('/api/v1/auth/login',data={'username':'dev-data-reader','password':'isolated-location-password'})
    client.headers['Authorization']='Bearer '+login.json()['access_token']
    assert [r['id'] for r in (await client.get('/api/v1/facilities')).json()['data']]==[str(f.id)]
    assert (await client.get('/api/v1/facilities/'+str(second.id))).status_code==404
    async with factory.begin() as db:
        changed=await db.get(Facility,f.id);changed.address='Reviewed different location'
    assert (await client.get('/api/v1/facilities/'+str(f.id))).json()['data'].get('location_context') is None
    async with factory.begin() as db:
        changed=await db.get(Facility,f.id);changed.address=f.address;changed.latitude=12;changed.longitude=77
    row=(await client.get('/api/v1/facilities/'+str(f.id))).json()['data']
    assert row['latitude']==12 and row.get('location_context') is None


@pytest.mark.asyncio
async def test_enrichment_replay_and_domain_invariants(api):
    _,factory,_=api
    async with factory.begin() as db:
        identity=await create_user(db,'admin','isolated-enrichment-password',[])
        owner=await db.get(User,UUID(identity['id']))
        with pytest.raises(ValueError,match='operations seed'):await enrich(db,owner,765)
        db.add_all([Facility(code=f'FD1-{i}',name=f'Source {i}') for i in range(2)])
        db.add(Medicine(code='MD1-1',name='Source medicine',unit='unspecified'));await db.flush()
        await seed_operations(db,owner,765,2,1)
        result=await enrich(db,owner,765)
        assert not result['reused'] and result['ambulances_added']==2 and result['maintenance_added']==2
        assert await db.scalar(select(func.count()).select_from(Ambulance))==2
        assert await db.scalar(select(func.count()).select_from(MaintenanceRecord))==2
        assert (await db.get(Shipment,UUID(result['shipment_id']))).status=='arrived'
        assert (await db.get(PurchaseOrder,UUID(result['order_id']))).status=='received'
        before={t.name:await db.scalar(select(func.count()).select_from(t)) for t in Base.metadata.sorted_tables}
        assert (await enrich(db,owner,765))['reused']
        after={t.name:await db.scalar(select(func.count()).select_from(t)) for t in Base.metadata.sorted_tables}
        assert before==after
        for row in await db.scalars(select(Inventory)):
            assert row.quantity==await db.scalar(select(func.sum(StockTransaction.quantity)).where(StockTransaction.inventory_id==row.id))
            assert row.reserved==0
