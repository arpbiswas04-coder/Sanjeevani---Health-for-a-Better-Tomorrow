from datetime import datetime,timezone,timedelta
import pytest
from sqlalchemy import select
from app.models import StockTransaction
from tests.test_platform import seed,receipt

pytestmark=pytest.mark.asyncio


async def test_reorder_policy_values_and_history(api):
    client,factory,_=api
    ids=await seed(client)
    policy='/api/v1/inventory/policies/'+ids['facility_id']+'/'+ids['medicine_id']
    body={'safety_stock':5,'lead_days':10,'minimum_history_days':7,'critical_days':2,'low_days':5}
    assert (await client.put(policy,json=body)).status_code==200
    no_history=(await client.get('/api/v1/inventory/days-of-stock',params=ids)).json()['data']
    assert no_history['suggested_quantity'] is None and no_history['reorder_point'] is None
    await client.post('/api/v1/inventory/receive',json=receipt(ids))
    async with factory.begin() as db:
        first=await db.scalar(select(StockTransaction).where(StockTransaction.kind=='receive'))
        first.created_at=datetime.now(timezone.utc)-timedelta(days=9)
    await client.post('/api/v1/inventory/issue',json={**ids,'quantity':8,'reference':'consumption'})
    result=(await client.get('/api/v1/inventory/days-of-stock',params={**ids,'window':10})).json()['data']
    assert result['average_daily_consumption']==pytest.approx(0.8)
    assert result['reorder_point']==13 and result['suggested_quantity']==11
    assert result['transferable_stock']==0 and result['status']=='low'
    assert (await client.put(policy,json={**body,'low_days':1})).status_code==422
