from datetime import datetime,timezone,timedelta
from uuid import UUID
import pytest
from sqlalchemy import select
from app.models import Inventory,MedicineBatch
from app.models.supply import Warehouse
from app.models.alerts import Alert
from app.services.alerts import evaluate_rule
from app.security.auth import access_token
from tests.test_platform import seed,receipt
from tests.test_transfers import prepare
from tests.test_operations_permissions import grant

pytestmark=pytest.mark.asyncio


async def test_zero_stock_policy_and_expiry_windows(api):
    client,factory,_=api
    ids=await seed(client)
    policy='/api/v1/inventory/policies/'+ids['facility_id']+'/'+ids['medicine_id']
    assert (await client.put(policy,json={'expiry_warning_days':3})).status_code==200
    for kind in ('LOW_STOCK','CRITICAL_STOCK'):
        rule=(await client.post('/api/v1/alert-rules',json={'facility_id':ids['facility_id'],'kind':kind,'threshold':0})).json()['data']['id']
        async with factory.begin() as db:
            assert await evaluate_rule(db,UUID(rule))==1
    await client.post('/api/v1/inventory/receive',json=receipt(ids,days=10))
    params={'facility_id':ids['facility_id']}
    assert (await client.get('/api/v1/inventory/expiry',params=params)).json()['data']==[]
    assert len((await client.get('/api/v1/inventory/expiry',params={**params,'days':20})).json()['data'])==1
    rule=(await client.post('/api/v1/alert-rules',json={'facility_id':ids['facility_id'],'kind':'EXPIRY','threshold':0,'window_days':90})).json()['data']['id']
    async with factory.begin() as db:
        assert await evaluate_rule(db,UUID(rule))==0
    await client.put(policy,json={'expiry_warning_days':20})
    assert len((await client.get('/api/v1/inventory/expiry',params=params)).json()['data'])==1
    async with factory.begin() as db:
        assert await evaluate_rule(db,UUID(rule))==1


async def test_transfer_enforces_safety_stock(api):
    client,_,_=api
    ids,_,identifier=await prepare(client,6)
    policy='/api/v1/inventory/policies/'+ids['facility_id']+'/'+ids['medicine_id']
    await client.put(policy,json={'safety_stock':5})
    url=f'/api/v1/transfers/{identifier}/actions'
    assert (await client.post(url,json={'action':'approve','reason':'Too much'})).status_code==409
    stock=(await client.get('/api/v1/inventory',params={'facility_id':ids['facility_id']})).json()['data'][0]
    assert stock['reserved']==0
    await client.put(policy,json={'safety_stock':4})
    assert (await client.post(url,json={'action':'approve','reason':'Exactly safe'})).status_code==200


async def test_warehouse_lifecycle_and_final_recall(api):
    client,factory,_=api
    ids=await seed(client)
    await client.patch('/api/v1/facilities/'+ids['facility_id'],json={'active':False})
    warehouse=(await client.post('/api/v1/warehouses',json={'facility_id':ids['facility_id']})).json()['data']
    assert warehouse['active'] is False
    await client.put('/api/v1/warehouses/'+warehouse['id'],json={'active':True})
    assert (await client.get('/api/v1/facilities/'+ids['facility_id'])).json()['data']['active'] is True
    await client.patch('/api/v1/facilities/'+ids['facility_id'],json={'active':False})
    async with factory() as db:
        assert (await db.get(Warehouse,UUID(warehouse['id']))).active is False
    assert (await client.patch('/api/v1/facilities/'+ids['facility_id'],json={'facility_type':'phc'})).status_code==409
    await client.patch('/api/v1/facilities/'+ids['facility_id'],json={'active':True})
    batch=(await client.post('/api/v1/inventory/receive',json=receipt(ids))).json()['data']['batch_id']
    recall=(await client.post('/api/v1/recalls',json={'batch_id':batch,'reason':'Defect','severity':'high'})).json()['data']['id']
    url='/api/v1/recalls/'+recall+'/resolve'
    assert (await client.post(url,json={'resolution':'Disposed'})).status_code==200
    assert (await client.post(url,json={'resolution':'Changed'})).status_code==409
    assert (await client.get('/api/v1/recalls')).json()['data'][0]['resolution']=='Disposed'


async def create_order(client,ids):
    supplier=(await client.post('/api/v1/suppliers',json={'name':'Supplier','code':'SUP'})).json()['data']['id']
    order=(await client.post('/api/v1/purchase-orders',json={'reference':'LIFECYCLE','supplier_id':supplier,'facility_id':ids['facility_id'],
        'items':[{'medicine_id':ids['medicine_id'],'quantity':10,'unit_price':'1.00'}]})).json()['data']['id']
    for action in ('submit','approve','order'):
        assert (await client.post('/api/v1/purchase-orders/'+order+'/actions',json={'action':action,'note':action})).status_code==200
    return order


async def test_order_shipment_cancellation_and_receipt(api):
    client,_,_=api
    ids=await seed(client)
    order=await create_order(client,ids)
    shipment={'reference':'S1','order_id':order,'origin':'Depot','expected_at':datetime.now(timezone.utc).isoformat()}
    sid=(await client.post('/api/v1/shipments',json=shipment)).json()['data']['id']
    cancel={'action':'cancel','note':'Cancel'}
    assert (await client.post('/api/v1/purchase-orders/'+order+'/actions',json=cancel)).status_code==409
    item=(await client.get('/api/v1/purchase-orders/'+order)).json()['data']['items'][0]['id']
    body={'item_id':item,'batch_number':'S1','quantity':1,'expires_on':str(datetime.now(timezone.utc).date()+timedelta(days=30)),'idempotency_key':'r1'}
    assert (await client.post('/api/v1/purchase-orders/'+order+'/receive',json=body)).status_code==409
    url='/api/v1/shipments/'+sid+'/actions'
    assert (await client.post(url,json={'status':'arrived','note':'Skip dispatch'})).status_code==409
    assert (await client.post(url,json={'status':'cancelled','note':'Cancelled'})).status_code==200
    assert (await client.post('/api/v1/purchase-orders/'+order+'/actions',json=cancel)).status_code==200
    assert (await client.post('/api/v1/purchase-orders/'+order+'/receive',json=body)).status_code==409
    assert (await client.post('/api/v1/shipments',json={**shipment,'reference':'S2'})).status_code==409
    assert (await client.post(url,json={'status':'dispatched','note':'Invalid'})).status_code==409


async def test_dispatched_order_cannot_be_cancelled(api):
    client,_,_=api
    ids=await seed(client)
    order=await create_order(client,ids)
    sid=(await client.post('/api/v1/shipments',json={'reference':'S1','order_id':order,'origin':'Depot','expected_at':datetime.now(timezone.utc).isoformat()})).json()['data']['id']
    url='/api/v1/shipments/'+sid+'/actions'
    assert (await client.post(url,json={'status':'dispatched','note':'Departed'})).status_code==200
    assert (await client.post('/api/v1/purchase-orders/'+order+'/actions',json={'action':'cancel','note':'Invalid'})).status_code==409
    assert (await client.post(url,json={'status':'cancelled','note':'Invalid'})).status_code==409


async def test_transfer_shipment_requires_both_scopes(api):
    client,factory,reader=api
    ids,destination,transfer=await prepare(client)
    await client.post('/api/v1/transfers/'+transfer+'/actions',json={'action':'approve','reason':'Approved'})
    body={'reference':'TS1','transfer_id':transfer,'origin':'Source','expected_at':datetime.now(timezone.utc).isoformat()}
    sid=(await client.post('/api/v1/shipments',json=body)).json()['data']['id']
    assert (await client.post('/api/v1/shipments/'+sid+'/actions',json={'status':'dispatched','note':'Transfer not dispatched'})).status_code==409
    await grant(factory,reader,destination,['procurement.read','procurement.write'])
    client.headers['Authorization']='Bearer '+access_token(reader)
    assert (await client.get('/api/v1/shipments')).json()['data']==[]
    assert (await client.get('/api/v1/shipments/'+sid+'/history')).status_code==404
    assert (await client.post('/api/v1/shipments/'+sid+'/actions',json={'status':'cancelled','note':'Unauthorized source'})).status_code==404
    assert (await client.post('/api/v1/shipments',json={**body,'reference':'TS2'})).status_code==404
