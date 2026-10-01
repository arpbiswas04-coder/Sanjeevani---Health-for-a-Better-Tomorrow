from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import select, func
from app.models import Inventory, StockTransaction
from tests.test_platform import seed, receipt
pytestmark = pytest.mark.asyncio


async def test_retry_adjustment_and_dos(api):
    client, factory, _ = api
    ids = await seed(client)
    payload = {**receipt(ids), 'idempotency_key': 'receive-1'}
    first = await client.post('/api/v1/inventory/receive', json=payload)
    assert first.status_code == 201
    assert (await client.post('/api/v1/inventory/receive', json=payload)).json() == first.json()
    assert (await client.post('/api/v1/inventory/receive', json={**payload,'quantity': 20})).status_code == 409
    batch = first.json()['data']['batch_id']
    adjustment = {'facility_id': ids['facility_id'], 'batch_id': batch, 'quantity': -3, 'kind': 'DAMAGE', 'reference': 'damaged', 'idempotency_key': 'damage-1'}
    assert (await client.post('/api/v1/inventory/adjust', json=adjustment)).status_code == 200
    assert (await client.post('/api/v1/inventory/adjust', json=adjustment)).status_code == 200
    assert (await client.post('/api/v1/inventory/adjust', json={**adjustment,'quantity': -20,'idempotency_key': 'bad'})).status_code == 409
    async with factory() as db:
        assert await db.scalar(select(Inventory.quantity)) == 7
        assert await db.scalar(select(func.sum(StockTransaction.quantity))) == 7
    assert (await client.get('/api/v1/inventory/days-of-stock', params=ids)).json()['data']['status'] == 'insufficient_history'
    async with factory.begin() as db:
        tx = await db.scalar(select(StockTransaction).where(StockTransaction.kind == 'receive'))
        tx.created_at = datetime.now(timezone.utc) - timedelta(days=10)
    assert (await client.get('/api/v1/inventory/days-of-stock', params=ids)).json()['data']['status'] == 'zero_consumption'
    await client.post('/api/v1/inventory/issue', json={**ids,'quantity': 2,'reference': 'consumption'})
    metrics = (await client.get('/api/v1/inventory/days-of-stock', params=ids)).json()['data']
    assert metrics['current_stock'] == 5
    assert metrics['days_of_stock'] == pytest.approx(27.5)


async def test_recall_trace_expiry(api):
    client, _, _ = api
    ids = await seed(client)
    received = (await client.post('/api/v1/inventory/receive', json=receipt(ids))).json()['data']
    batch = received['batch_id']
    response = await client.post('/api/v1/recalls', json={'batch_id': batch, 'reason': 'Manufacturer recall', 'severity': 'critical'})
    assert response.status_code == 201
    assert (await client.post('/api/v1/inventory/issue', json={**ids,'quantity': 1,'reference': 'blocked'})).status_code == 409
    trace = (await client.get(f'/api/v1/batches/{batch}/trace')).json()['data']
    assert trace['batch']['recalled'] is True and len(trace['transactions']) == 1
    assert len((await client.get('/api/v1/inventory/expiry', params={'facility_id': ids['facility_id']})).json()['data']) == 1
    assert (await client.post('/api/v1/recalls/' + response.json()['data']['id'] + '/resolve', json={'resolution': 'Disposed'})).status_code == 200
    assert (await client.post('/api/v1/inventory/issue', json={**ids,'quantity': 1,'reference': 'still-blocked'})).status_code == 409
