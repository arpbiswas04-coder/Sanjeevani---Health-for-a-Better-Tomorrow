from datetime import datetime,timezone,timedelta
import pytest
from tests.test_platform import seed
pytestmark=pytest.mark.asyncio


async def test_procurement_warehouse_and_shipments(api):
    client,_,_=api
    ids=await seed(client)
    supplier=await client.post('/api/v1/suppliers',json={'name':'Supplier','code':'SUP1'})
    assert supplier.status_code==201
    supplier_id=supplier.json()['data']['id']
    assert (await client.get(f'/api/v1/suppliers/{supplier_id}/metrics')).json()['data']['fulfilment_rate'] is None
    warehouse=await client.post('/api/v1/warehouses',json={'facility_id':ids['facility_id'],'capacity_units':1000})
    assert warehouse.status_code==201
    order=await client.post('/api/v1/purchase-orders',json={'reference':'PO1','supplier_id':supplier_id,'facility_id':ids['facility_id'],
        'items':[{'medicine_id':ids['medicine_id'],'quantity':10,'unit_price':'2.50'}]})
    assert order.status_code==201,order.text
    oid=order.json()['data']['id']
    for action in ('submit','approve','order'):
        assert (await client.post(f'/api/v1/purchase-orders/{oid}/actions',json={'action':action,'note':action})).status_code==200
    shipment=await client.post('/api/v1/shipments',json={'reference':'SHIP1','order_id':oid,'origin':'Supplier depot',
        'expected_at':(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()})
    assert shipment.status_code==201,shipment.text
    sid=shipment.json()['data']['id']
    for status in ('dispatched','in_transit','arrived'):
        assert (await client.post(f'/api/v1/shipments/{sid}/actions',json={'status':status,'note':status})).status_code==200
    assert len((await client.get(f'/api/v1/shipments/{sid}/history')).json()['data'])==4
    item=(await client.get(f'/api/v1/purchase-orders/{oid}')).json()['data']['items'][0]['id']
    receipt={'item_id':item,'batch_number':'POB','expires_on':str(datetime.now(timezone.utc).date()+timedelta(days=30)),
             'quantity':6,'idempotency_key':'po-receive-1'}
    first=await client.post(f'/api/v1/purchase-orders/{oid}/receive',json=receipt)
    assert first.status_code==200,first.text
    assert first.json()['data']['order']['status']=='partially_received'
    assert (await client.post(f'/api/v1/purchase-orders/{oid}/receive',json=receipt)).json()==first.json()
    assert (await client.post(f'/api/v1/purchase-orders/{oid}/receive',json={**receipt,'idempotency_key':'excess','quantity':5})).status_code==409
    final=await client.post(f'/api/v1/purchase-orders/{oid}/receive',json={**receipt,'idempotency_key':'final','quantity':4})
    assert final.json()['data']['order']['status']=='received'
    wid=warehouse.json()['data']['id']
    assert (await client.get(f'/api/v1/warehouses/{wid}/inventory')).json()['data'][0]['quantity']==10
    metrics=(await client.get(f'/api/v1/suppliers/{supplier_id}/metrics')).json()['data']
    assert metrics['fulfilment_rate']==1 and metrics['quantity_fulfilment_rate']==1

async def test_procurement_approval_requires_explicit_permission(api):
    from sqlalchemy import select,delete
    from app.models import Permission,RolePermission
    client,factory,_=api
    ids=await seed(client)
    supplier=(await client.post('/api/v1/suppliers',json={'name':'Supplier','code':'SUP1'})).json()['data']['id']
    order=(await client.post('/api/v1/purchase-orders',json={'reference':'PO1','supplier_id':supplier,'facility_id':ids['facility_id'],
        'items':[{'medicine_id':ids['medicine_id'],'quantity':1,'unit_price':'1.00'}]})).json()['data']['id']
    await client.post(f'/api/v1/purchase-orders/{order}/actions',json={'action':'submit','note':'Submitted'})
    async with factory.begin() as db:
        permission=await db.scalar(select(Permission).where(Permission.name=='procurement.approve'))
        await db.execute(delete(RolePermission).where(RolePermission.permission_id==permission.id))
    assert (await client.post(f'/api/v1/purchase-orders/{order}/actions',json={'action':'approve','note':'Unauthorized'})).status_code==403
    assert (await client.get(f'/api/v1/purchase-orders/{order}')).json()['data']['status']=='submitted'
