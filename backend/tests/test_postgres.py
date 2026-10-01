"""Opt-in PostgreSQL concurrency tests; never use an application database."""
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import text,select,func,update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.database import Base
from app.models import User,Facility,Medicine,Inventory,StockTransaction
from app.schemas.platform import Receive,Issue
from app.services.inventory import receive,issue
from app.services.geography import nearby

TEST_URL=os.environ.get('TEST_DATABASE_URL')
pytestmark=[pytest.mark.asyncio,pytest.mark.skipif(not TEST_URL,reason='TEST_DATABASE_URL not configured; requires disposable PostgreSQL/PostGIS database ending _test')]


@pytest_asyncio.fixture
async def pg():
    assert make_url(TEST_URL).database.endswith('_test'),'Refusing to run PostgreSQL tests outside a database ending _test'
    schema='test_'+uuid4().hex
    admin=create_async_engine(TEST_URL)
    async with admin.begin() as conn:
        available=await conn.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')"))
        assert available, 'Install PostGIS in the disposable test database before running PostgreSQL tests'
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine=create_async_engine(TEST_URL,execution_options={'schema_translate_map':{None:schema}})
    try:
        result=await asyncio.to_thread(subprocess.run,[sys.executable,'-m','alembic','upgrade','head'],
            cwd=Path(__file__).resolve().parents[1],env={**os.environ,'DATABASE_URL':TEST_URL,'ALEMBIC_TEST_SCHEMA':schema},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        factory=async_sessionmaker(engine,expire_on_commit=False)
        async with factory.begin() as db:
            user=User(username='tester',password_hash='not-used',scope_mode='global')
            facility=Facility(name='Test',code='T1',latitude=22.5,longitude=88.3)
            medicine=Medicine(name='Test',code='M1',unit='tablet')
            db.add_all([user,facility,medicine])
            await db.flush()
        yield factory,user,facility,medicine
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            # schema is exclusively a freshly generated UUID namespace.
            assert schema.startswith('test_') and len(schema)==37
            await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()


async def test_postgres_competing_stock_writers(pg):
    factory,user,facility,medicine=pg
    async with factory.begin() as db:
        await receive(db,Receive(facility_id=facility.id,medicine_id=medicine.id,batch_number='B1',
            expires_on=datetime.now(timezone.utc).date()+timedelta(days=30),quantity=10,reference='test'),user)
    async def dispense():
        try:
            async with factory.begin() as db:
                await issue(db,Issue(facility_id=facility.id,medicine_id=medicine.id,quantity=7,reference='race'),user)
            return 'ok'
        except HTTPException as exc:
            return exc.status_code
    results=await asyncio.gather(dispense(),dispense())
    assert sorted(results,key=str)==sorted(['ok',409],key=str)
    async with factory() as db:
        assert await db.scalar(select(Inventory.quantity))==3
        assert await db.scalar(select(func.sum(StockTransaction.quantity)))==3


async def test_postgis_distance(pg):
    factory,user,facility,_=pg
    async with factory() as db:
        rows=await nearby(db,user,22.5,88.3,10,10)
        assert len(rows)==1 and rows[0]['distance_km']==pytest.approx(0)
        schema=db.bind.get_execution_options()['schema_translate_map'][None]
        index=await db.scalar(text("SELECT indexname FROM pg_indexes WHERE schemaname=:schema AND indexname='ix_facilities_geography'"),{'schema':schema})
        assert index=='ix_facilities_geography'


async def test_postgres_ledger_cannot_be_rewritten(pg):
    factory,user,facility,medicine=pg
    async with factory.begin() as db:
        await receive(db,Receive(facility_id=facility.id,medicine_id=medicine.id,batch_number='IMMUTABLE',
            expires_on=datetime.now(timezone.utc).date()+timedelta(days=30),quantity=10,reference='immutability'),user)
    with pytest.raises(DBAPIError):
        async with factory.begin() as db:
            await db.execute(update(StockTransaction).values(quantity=999))
    async with factory() as db:
        assert await db.scalar(select(func.sum(StockTransaction.quantity)))==10


async def test_postgres_sync_commit_order(pg):
    from app.schemas.operations import AggregateInput
    from app.services.operations import aggregate
    from app.services.sync import pull
    factory,user,facility,_=pg
    payload=AggregateInput(facility_id=facility.id,day=datetime.now(timezone.utc).date(),category='outpatient',count=1)
    async with factory() as first:
        await first.begin()
        await aggregate(first,user,'footfall',payload)
        async with factory() as reader:
            before=await pull(reader,user,'footfall',0,None,10)
            assert before['watermark']==0 and before['items']==[]
        async def competing():
            async with factory.begin() as db:
                await aggregate(db,user,'footfall',payload.model_copy(update={'expected_version':1,'count':2}))
        task=asyncio.create_task(competing())
        await asyncio.sleep(0.05)
        assert not task.done()
        await first.commit()
        await asyncio.wait_for(task,10)
    async with factory() as db:
        result=await pull(db,user,'footfall',before['watermark'],None,10)
        assert [r['count'] for r in result['items']]==[1,2]
        assert result['watermark']==2


@pytest.mark.skipif(os.environ.get('ENABLE_TIMESCALEDB')!='1',reason='ENABLE_TIMESCALEDB=1 and a TimescaleDB/PostGIS test server are required')
async def test_postgres_timescale_hypertable(pg):
    from app.schemas.operations import TemperatureInput
    from app.services.operations import temperature,cold_chain_series
    factory,user,facility,_=pg
    now=datetime.now(timezone.utc)
    async with factory.begin() as db:
        await temperature(db,user,TemperatureInput(facility_id=facility.id,observed_at=now,temperature=9,minimum=2,maximum=8,source='pg-sensor',external_id='1'))
    async with factory() as db:
        schema=db.bind.get_execution_options()['schema_translate_map'][None]
        count=await db.scalar(text("SELECT count(*) FROM timescaledb_information.hypertables WHERE hypertable_schema=:schema AND hypertable_name='cold_chain_samples'"),{'schema':schema})
        assert count==1
        rows=await cold_chain_series(db,user,facility.id,now-timedelta(hours=1),now+timedelta(hours=1),0,10)
        assert len(rows)==1 and rows[0]['temperature']==9
