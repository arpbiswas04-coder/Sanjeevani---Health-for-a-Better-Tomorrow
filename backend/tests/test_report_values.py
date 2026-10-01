import csv
from io import StringIO,BytesIO
from datetime import datetime,timezone,timedelta
from uuid import UUID
import pytest
from sqlalchemy import select
from openpyxl import load_workbook
from app.models import MedicineBatch,User
from app.models.supply import Supplier,PurchaseOrder,PurchaseOrderItem,Shipment
from tests.test_platform import seed,receipt

pytestmark=pytest.mark.asyncio


async def test_stock_expiry_and_export_values(api):
    client,factory,_=api
    ids=await seed(client)
    for batch in ('PAST','SOON'):
        await client.post('/api/v1/inventory/receive',json=receipt(ids,batch=batch,days=10))
    async with factory.begin() as db:
        batch=await db.scalar(select(MedicineBatch).where(MedicineBatch.batch_number=='PAST'))
        batch.expires_on=datetime.now(timezone.utc).date()-timedelta(days=1)
    rows=(await client.get('/api/v1/reports/expiry')).json()['data']['rows']
    assert {r['expiry_state'] for r in rows}=={'expired','upcoming'}
    assert {r['batch_number']:r['available'] for r in rows}=={'PAST':0,'SOON':10}
    for row in rows:
        assert row['medicine_id']==ids['medicine_id'] and row['facility_id']==ids['facility_id']
        assert row['medicine_name'] and row['facility_name'] and row['expires_on'] and row['quantity']==10
    assert len((await client.get('/api/v1/reports/expiry',params={'status':'upcoming'})).json()['data']['rows'])==1
    csv_response=await client.get('/api/v1/reports/stock',params={'format':'csv'})
    csv_rows=list(csv.DictReader(StringIO(csv_response.content.decode('utf-8-sig'))))
    assert {r['batch_number'] for r in csv_rows}=={'PAST','SOON'}
    assert all(r['quantity']=='10' for r in csv_rows)
    xlsx=await client.get('/api/v1/reports/expiry',params={'format':'xlsx'})
    values=list(load_workbook(BytesIO(xlsx.content),read_only=True).active.values)
    headers=list(values[0]); records=[dict(zip(headers,r)) for r in values[1:]]
    assert {r['expiry_state'] for r in records}=={'expired','upcoming'}


async def test_supplier_metric_denominators_and_delay(api):
    client,factory,_=api
    ids=await seed(client)
    now=datetime.now(timezone.utc)
    async with factory.begin() as db:
        user=await db.scalar(select(User).where(User.username=='admin'))
        supplier=Supplier(name='Metrics',code='MET')
        db.add(supplier); await db.flush()
        orders=[]
        for i,(status,quantity,received) in enumerate([('received',10,10),('partially_received',10,4),('ordered',10,0),('cancelled',100,0),('draft',100,0)]):
            order=PurchaseOrder(reference=f'MET-{i}',supplier_id=supplier.id,facility_id=UUID(ids['facility_id']),created_by=user.id,status=status)
            db.add(order);await db.flush();orders.append(order)
            db.add(PurchaseOrderItem(order_id=order.id,medicine_id=UUID(ids['medicine_id']),quantity=quantity,received=received,unit_price=1))
        for i,days in enumerate([2,-1]):
            db.add(Shipment(reference=f'SHIP-{i}',order_id=orders[i].id,supplier_id=supplier.id,facility_id=UUID(ids['facility_id']),origin='Depot',transport={},status='arrived',expected_at=now-timedelta(days=3),arrived_at=now-timedelta(days=3)+timedelta(days=days)))
    result=(await client.get('/api/v1/suppliers/'+str(supplier.id)+'/metrics')).json()['data']
    assert result['order_count']==5 and result['eligible_order_count']==3
    assert result['fulfilment_rate']==pytest.approx(1/3)
    assert result['quantity_fulfilment_rate']==pytest.approx(14/30)
    assert result['average_delivery_delay_days']==pytest.approx(1)
    assert 'quantity_accuracy' not in result
