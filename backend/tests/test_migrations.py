import os
import subprocess
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine,inspect


def test_migrations_from_empty_database(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    env={**os.environ,'DATABASE_URL':'sqlite+aiosqlite:///'+str(tmp_path/'migration.db')}
    for args in (['upgrade','head'],['check'],['heads']):
        result=subprocess.run([sys.executable,'-m','alembic',*args],cwd=backend,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
    engine=create_engine('sqlite:///'+str(tmp_path/'migration.db'))
    with engine.connect() as connection:
        tables=set(inspect(connection).get_table_names())
        assert {'users','alerts','shipments','stock_transactions','population_snapshots','backup_records'}<=tables
    engine.dispose()


def test_postgresql_migration_sql_compiles(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    env={**os.environ,'DATABASE_URL':'postgresql+asyncpg://offline@localhost/offline'}
    result=subprocess.run([sys.executable,'-m','alembic','upgrade','head','--sql'],cwd=backend,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'CREATE EXTENSION IF NOT EXISTS postgis' in result.stdout
    assert 'immutable_stock_transactions' in result.stdout


def test_populated_sync_and_telemetry_backfill(tmp_path):
    from datetime import datetime,timezone,date
    from uuid import uuid4
    import json
    from sqlalchemy import select,text
    from app.models import Facility,PatientFootfall,TemperatureObservation,Warehouse
    backend=Path(__file__).resolve().parents[1]
    path=tmp_path/'backfill.db'
    env={**os.environ,'DATABASE_URL':'sqlite+aiosqlite:///'+str(path),'ENABLE_TIMESCALEDB':'1'}
    result=subprocess.run([sys.executable,'-m','alembic','upgrade','f92e36664324'],cwd=backend,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    engine=create_engine('sqlite:///'+str(path))
    fid,aid,tid=uuid4(),uuid4(),uuid4()
    now=datetime.now(timezone.utc)
    with engine.begin() as db:
        db.execute(Facility.__table__.insert().values(id=fid,name='Existing',code='OLD',active=False,facility_type='warehouse'))
        db.execute(Warehouse.__table__.insert().values(facility_id=fid,active=True,capacity={}))
        db.execute(PatientFootfall.__table__.insert().values(id=aid,facility_id=fid,day=now.date(),category='outpatient',count=12,version=3))
        db.execute(TemperatureObservation.__table__.insert().values(id=tid,facility_id=fid,observed_at=now,temperature=9,minimum=2,maximum=8,source='sensor',external_id='old',excursion=True))
    result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=backend,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    with engine.connect() as db:
        change=db.execute(text('SELECT sequence,payload FROM sync_changes')).one()
        assert change.sequence==1
        payload=json.loads(change.payload)
        assert payload['id']==str(aid) and payload['count']==12 and payload['version']==3
        assert db.scalar(text('SELECT sequence FROM sync_clock'))==1
        assert db.scalar(text('SELECT temperature FROM cold_chain_samples'))==9
        assert db.scalar(text('SELECT COUNT(*) FROM temperature_observations'))==1
        assert db.scalar(text('SELECT active FROM warehouses'))==0
    engine.dispose()
