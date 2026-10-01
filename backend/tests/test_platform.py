from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select, func
from app.models import AuditLog, Inventory, MedicineBatch, StockTransaction
from app.security.auth import access_token

pytestmark = pytest.mark.asyncio


async def seed(client):
    facility = await client.post('/api/v1/facilities', json={'name': 'PHC', 'code': 'PHC1'})
    medicine = await client.post('/api/v1/medicines', json={'name': 'Medicine', 'code': 'MED1', 'unit': 'tablet'})
    assert facility.status_code == medicine.status_code == 201
    return {'facility_id': facility.json()['data']['id'], 'medicine_id': medicine.json()['data']['id']}


def receipt(ids, batch='A', days=30, quantity=10):
    return {**ids, 'batch_number': batch, 'expires_on': str(datetime.now(timezone.utc).date() + timedelta(days=days)),
            'quantity': quantity, 'reference': 'delivery-1'}


async def test_auth_and_permissions(api):
    client, _, reader = api
    response = await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code == 401
    assert response.json()['success'] is False
    response = await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password'})
    assert response.status_code == 200
    client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    assert (await client.get('/api/v1/auth/me')).json()['data']['username'] == 'admin'
    client.headers['Authorization'] = 'Bearer ' + access_token(reader)
    assert (await client.get('/api/v1/facilities')).status_code == 403
    client.headers['Authorization'] = 'Bearer broken'
    assert (await client.get('/api/v1/facilities')).status_code == 401
    client.headers.clear()
    assert (await client.get('/api/v1/facilities')).status_code == 401


async def test_fefo_and_ledger(api):
    client, factory, _ = api
    ids = await seed(client)
    late = await client.post('/api/v1/inventory/receive', json=receipt(ids, 'late', 60))
    early = await client.post('/api/v1/inventory/receive', json=receipt(ids, 'early', 20))
    assert late.status_code == early.status_code == 201
    response = await client.post('/api/v1/inventory/issue', json={**ids, 'quantity': 12, 'reference': 'dispense-1'})
    assert response.status_code == 200
    allocations = response.json()['data']['allocations']
    assert allocations == [{'batch_id': early.json()['data']['batch_id'], 'quantity': 10},
                           {'batch_id': late.json()['data']['batch_id'], 'quantity': 2}]
    async with factory() as db:
        balance = await db.scalar(select(func.sum(Inventory.quantity)))
        ledger = await db.scalar(select(func.sum(StockTransaction.quantity)))
        assert balance == ledger == 8
        assert await db.scalar(select(func.count()).select_from(AuditLog)) == 5
    response = await client.get('/api/v1/inventory/transactions', params={'facility_id': ids['facility_id']})
    assert len(response.json()['data']) == 4


async def test_insufficient_stock_rolls_back(api):
    client, factory, _ = api
    ids = await seed(client)
    await client.post('/api/v1/inventory/receive', json=receipt(ids))
    response = await client.post('/api/v1/inventory/issue', json={**ids, 'quantity': 11, 'reference': 'too-much'})
    assert response.status_code == 409
    async with factory() as db:
        assert await db.scalar(select(Inventory.quantity)) == 10
        assert await db.scalar(select(func.count()).select_from(StockTransaction)) == 1


async def test_expired_recalled_and_conflicting_batches(api):
    client, factory, _ = api
    ids = await seed(client)
    assert (await client.post('/api/v1/inventory/receive', json=receipt(ids, days=0))).status_code == 422
    assert (await client.post('/api/v1/inventory/receive', json=receipt(ids, quantity=-1))).status_code == 422
    await client.post('/api/v1/inventory/receive', json=receipt(ids))
    assert (await client.post('/api/v1/inventory/receive', json=receipt(ids, days=40))).status_code == 409
    async with factory.begin() as db:
        batch = await db.scalar(select(MedicineBatch))
        batch.recalled = True
    assert (await client.post('/api/v1/inventory/issue', json={**ids, 'quantity': 1, 'reference': 'recalled'})).status_code == 409
    assert (await client.post('/api/v1/inventory/receive', json=receipt(ids))).status_code == 409
    async with factory.begin() as db:
        batch = await db.scalar(select(MedicineBatch))
        batch.recalled = False
        batch.expires_on = datetime.now(timezone.utc).date()
    assert (await client.post('/api/v1/inventory/issue', json={**ids, 'quantity': 1, 'reference': 'expired'})).status_code == 409


async def test_duplicates_validation_and_openapi(api):
    client, _, _ = api
    await seed(client)
    assert (await client.post('/api/v1/facilities', json={'name': 'Duplicate', 'code': 'PHC1'})).status_code == 409
    assert (await client.post('/api/v1/facilities', json={'name': ' ', 'code': 'EMPTY'})).status_code == 422
    response = await client.get('/api/v1/openapi.json')
    assert response.status_code == 200
    assert '/api/v1/inventory/issue' in response.json()['paths']

async def test_expired_and_wrongly_signed_tokens(api):
    import jwt
    from app.core.config import settings
    client, _, reader = api
    now = datetime.now(timezone.utc)
    claims = {'sub': str(reader), 'iat': now - timedelta(hours=1),
              'exp': now - timedelta(minutes=1), 'iss': 'sanjeevani', 'type': 'access'}
    client.headers['Authorization'] = 'Bearer ' + jwt.encode(claims, settings.JWT_SECRET, algorithm='HS256')
    assert (await client.get('/api/v1/auth/me')).status_code == 401
    claims['exp'] = now + timedelta(minutes=5)
    client.headers['Authorization'] = 'Bearer ' + jwt.encode(claims, 'different-signing-key-at-least-32-characters', algorithm='HS256')
    assert (await client.get('/api/v1/auth/me')).status_code == 401


async def test_missing_resources_and_receipt_accumulation(api):
    from uuid import uuid4
    client, factory, _ = api
    ids = await seed(client)
    missing = {**ids, 'medicine_id': str(uuid4())}
    assert (await client.post('/api/v1/inventory/receive', json=receipt(missing))).status_code == 404
    for _ in range(2):
        assert (await client.post('/api/v1/inventory/receive', json=receipt(ids))).status_code == 201
    async with factory() as db:
        assert await db.scalar(select(Inventory.quantity)) == 20
        assert await db.scalar(select(func.sum(StockTransaction.quantity))) == 20
        assert await db.scalar(select(func.count()).select_from(MedicineBatch)) == 1
