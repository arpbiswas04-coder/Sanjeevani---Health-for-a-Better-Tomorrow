"""Consumer mutation regressions; all state lives in disposable test databases."""
from datetime import datetime, timedelta, timezone
from uuid import UUID
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import User, Role, Permission, UserRole, RolePermission, Facility, Inventory, StockTransaction, AuditLog
from app.models.identity import UserFacility
from app.security.auth import access_token
from tests.test_postgres import pg, TEST_URL
from tests.test_platform import seed, receipt

pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(not TEST_URL, reason='Disposable PostgreSQL TEST_DATABASE_URL not configured')
async def test_postgres_mutation_authorization_replay_and_rollback(pg, monkeypatch):
    factory, user, facility, medicine = pg
    monkeypatch.setattr(settings, 'APP_ENV', 'testing')
    async with factory.begin() as db:
        stored = await db.get(User, user.id)
        stored.scope_mode = 'restricted'
        writer = Role(name='phase4_writer')
        reader_role = Role(name='phase4_reader')
        reader = User(username='phase4-reader', password_hash='not-used', scope_mode='restricted')
        other = Facility(name='Other scope', code='P4-OTHER')
        db.add_all([writer, reader_role, reader, other]); await db.flush()
        grants = {p.name:p for p in await db.scalars(select(Permission))}
        db.add_all([UserRole(user_id=user.id,role_id=writer.id), UserRole(user_id=reader.id,role_id=reader_role.id),
                    RolePermission(role_id=writer.id,permission_id=grants['inventory.write'].id),
                    RolePermission(role_id=writer.id,permission_id=grants['inventory.read'].id),
                    RolePermission(role_id=reader_role.id,permission_id=grants['inventory.read'].id),
                    UserFacility(user_id=user.id,facility_id=facility.id),UserFacility(user_id=reader.id,facility_id=facility.id)])
    async def database():
        async with factory.begin() as db:
            yield db
    app.dependency_overrides[get_db] = database
    body={'facility_id':str(facility.id),'medicine_id':str(medicine.id),'batch_number':'P4',
          'expires_on':str(datetime.now(timezone.utc).date()+timedelta(days=60)),
          'quantity':10,'reference':'P4 receipt','idempotency_key':'p4-receipt'}
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
            client.headers['Authorization']='Bearer '+access_token(user.id)
            first=await client.post('/api/v1/inventory/receive',json=body)
            assert first.status_code==201
            assert (await client.post('/api/v1/inventory/receive',json=body)).json()==first.json()
            assert (await client.post('/api/v1/inventory/receive',json={**body,'quantity':11})).status_code==409
            issue={k:body[k] for k in ('facility_id','medicine_id','reference')}
            issue.update(quantity=3,idempotency_key='p4-issue')
            assert (await client.post('/api/v1/inventory/issue',json=issue)).status_code==200
            assert (await client.post('/api/v1/inventory/issue',json=issue)).status_code==200
            assert (await client.post('/api/v1/inventory/issue',json={**issue,'quantity':8,'idempotency_key':'p4-excess'})).status_code==409
            assert (await client.post('/api/v1/inventory/receive',json={**body,'quantity':0})).status_code==422
            assert (await client.post('/api/v1/inventory/receive',json={**body,'facility_id':str(other.id)})).status_code==404
            client.headers['Authorization']='Bearer '+access_token(reader.id)
            assert (await client.post('/api/v1/inventory/receive',json=body)).status_code==403
            client.headers['Authorization']='Bearer invalid-session'
            assert (await client.post('/api/v1/inventory/receive',json=body)).status_code==401
        async with factory() as db:
            assert await db.scalar(select(Inventory.quantity))==7
            assert await db.scalar(select(func.count()).select_from(StockTransaction))==2
            assert await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action.like('inventory.%')))==2
    finally:
        app.dependency_overrides.pop(get_db,None)


async def test_procurement_unique_reference_and_receipt_idempotency(api):
    client,factory,_=api
    ids=await seed(client)
    supplier=(await client.post('/api/v1/suppliers',json={'name':'Phase 4 supplier','code':'P4-SUP'})).json()['data']
    body={'supplier_id':supplier['id'],'facility_id':ids['facility_id'],'reference':'P4-PO','items':[{'medicine_id':ids['medicine_id'],'quantity':5,'unit_price':'1.25'}]}
    response=await client.post('/api/v1/purchase-orders',json=body)
    assert response.status_code==201
    identifier=response.json()['data']['id']
    assert (await client.post('/api/v1/purchase-orders',json=body)).status_code==409
    for action in ['submit','approve','order']:
        assert (await client.post(f'/api/v1/purchase-orders/{identifier}/actions',json={'action':action,'note':'P4 verification'})).status_code==200
    detail=(await client.get(f'/api/v1/purchase-orders/{identifier}')).json()['data']
    payload={'item_id':detail['items'][0]['id'],'batch_number':'P4-B','expires_on':receipt(ids)['expires_on'],'quantity':5,'idempotency_key':'P4-PO-receipt'}
    url=f'/api/v1/purchase-orders/{identifier}/receive'
    first=await client.post(url,json=payload)
    assert first.status_code==200 and first.json()['data']['order']['status']=='received'
    assert (await client.post(url,json=payload)).json()==first.json()
    async with factory() as db:
        assert await db.scalar(select(func.sum(Inventory.quantity)))==5
        assert await db.scalar(select(func.count()).select_from(StockTransaction))==1


async def test_report_request_retry_and_independent_snapshots(api):
    client,_,_=api
    ids=await seed(client)
    payload={'facility_id':ids['facility_id'],'kind':'stock','format':'csv'}
    keyed={**payload,'idempotency_key':'report-retry'}
    original=await client.post('/api/v1/report-jobs',json=keyed)
    assert original.status_code==202
    assert (await client.post('/api/v1/report-jobs',json=keyed)).json()==original.json()
    assert (await client.post('/api/v1/report-jobs',json={**keyed,'format':'pdf'})).status_code==409
    first=await client.post('/api/v1/report-jobs',json=payload)
    second=await client.post('/api/v1/report-jobs',json=payload)
    assert first.status_code==second.status_code==202
    assert first.json()['data']['status']=='pending'
    assert first.json()['data']['id']!=second.json()['data']['id']
    assert (await client.get('/api/v1/report-jobs/'+first.json()['data']['id']+'/download')).status_code==409
