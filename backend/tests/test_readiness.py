"""Readiness regressions using disposable PostgreSQL namespaces."""
import asyncio
import pytest
from sqlalchemy import select,func
from tests.test_postgres import pg,TEST_URL
from app.models import UserRole,Role,RolePermission,Permission,AuditLog
from app.models.report_jobs import ReportJob
from app.schemas.report_jobs import ReportJobRequest
from app.services.report_jobs import request,generate_pending


@pytest.mark.asyncio
@pytest.mark.parametrize('missing',['REDIS_URL','FRONTEND_URL','BACKEND_URL','BACKEND_CORS_ORIGINS'])
async def test_production_rejects_implicit_local_configuration(monkeypatch,missing):
    import app.main as main
    from app.core.config import Settings
    values={'APP_ENV':'production','DATABASE_URL':'postgresql+asyncpg://unused:unused@localhost/readiness_test',
            'REDIS_URL':'redis://localhost:6379/15','FRONTEND_URL':'https://ui.example.invalid',
            'BACKEND_URL':'https://api.example.invalid','BACKEND_CORS_ORIGINS':['https://ui.example.invalid'],
            'JWT_SECRET':'test-only-explicit-configuration-secret'}
    values.pop(missing)
    monkeypatch.delenv(missing,raising=False)
    config=Settings(_env_file=None,**values)
    monkeypatch.setattr(main,'settings',config)
    with pytest.raises(RuntimeError,match=missing):
        async with main.lifespan(main.app):
            pytest.fail('Production accepted an implicit development setting')


@pytest.mark.asyncio
async def test_production_accepts_explicit_configuration(monkeypatch):
    import app.main as main
    from app.core.config import Settings
    config=Settings(_env_file=None,APP_ENV='production',DATABASE_URL='postgresql+asyncpg://unused:unused@localhost/readiness_test',
        REDIS_URL='redis://localhost:6379/15',FRONTEND_URL='https://ui.example.invalid',
        BACKEND_URL='https://api.example.invalid',BACKEND_CORS_ORIGINS=['https://ui.example.invalid'],
        JWT_SECRET='test-only-explicit-configuration-secret')
    monkeypatch.setattr(main,'settings',config)
    async with main.lifespan(main.app):
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(not TEST_URL,reason='Disposable PostgreSQL TEST_DATABASE_URL not configured')
async def test_concurrent_report_retry_and_generation(pg):
    factory,user,facility,_=pg
    async with factory.begin() as db:
        role=Role(name='readiness_reports')
        db.add(role); await db.flush()
        db.add(UserRole(user_id=user.id,role_id=role.id))
        for permission in await db.scalars(select(Permission).where(Permission.name.in_(['reports.read','reports.export']))):
            db.add(RolePermission(role_id=role.id,permission_id=permission.id))
    payload=ReportJobRequest(facility_id=facility.id,kind='stock',idempotency_key='concurrent-report')
    async def create():
        async with factory.begin() as db:
            return await request(db,user,payload)
    first,second=await asyncio.gather(create(),create())
    assert str(first['id'])==str(second['id'])
    async def generate():
        async with factory.begin() as db:
            return await generate_pending(db)
    assert sum(await asyncio.gather(generate(),generate()))==1
    assert await generate()==0
    async with factory() as db:
        assert await db.scalar(select(func.count()).select_from(ReportJob))==1
        assert await db.scalar(select(ReportJob.status))=='completed'
        for action in ['report.requested','report.completed']:
            assert await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action==action))==1


@pytest.mark.asyncio
@pytest.mark.skipif(not TEST_URL,reason='Disposable PostgreSQL TEST_DATABASE_URL not configured')
async def test_concurrent_transfer_dispatch_deducts_once(pg):
    from datetime import datetime,timedelta,timezone
    from fastapi import HTTPException
    from app.models import Facility,Inventory,StockTransaction
    from app.schemas.platform import Receive
    from app.schemas.transfers import TransferCreate,TransferAction
    from app.services.inventory import receive
    from app.services.transfers import create,transition
    factory,user,facility,medicine=pg
    async with factory.begin() as db:
        destination=Facility(code='RACE-DEST',name='Transfer race destination')
        db.add(destination);await db.flush()
        received=await receive(db,Receive(facility_id=facility.id,medicine_id=medicine.id,
            batch_number='RACE',expires_on=datetime.now(timezone.utc).date()+timedelta(days=30),quantity=10,reference='setup'),user)
        transfer=await create(db,user,TransferCreate(source_id=facility.id,destination_id=destination.id,
            reference='race',idempotency_key='create-race',items=[{'batch_id':received['batch_id'],'quantity':5}]))
        await transition(db,user,transfer['id'],TransferAction(action='approve',reason='setup'))
    async def dispatch():
        try:
            async with factory.begin() as db:
                await transition(db,user,transfer['id'],TransferAction(action='dispatch',reason='race'))
            return 200
        except HTTPException as error:return error.status_code
    assert sorted(await asyncio.gather(dispatch(),dispatch()))==[200,409]
    async with factory() as db:
        stock=await db.scalar(select(Inventory).where(Inventory.facility_id==facility.id))
        assert stock.quantity==5 and stock.reserved==0
        assert await db.scalar(select(func.count()).select_from(StockTransaction).where(StockTransaction.kind=='TRANSFER_OUT'))==1
