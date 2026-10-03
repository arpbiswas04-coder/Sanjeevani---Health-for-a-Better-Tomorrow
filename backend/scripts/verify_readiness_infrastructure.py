"""Isolated empty-database, real Celery worker/Beat and HTTP readiness probe.

Run from backend with its .venv. Reads TEST_DATABASE_URL / TEST_REDIS_URL
from .env.local. Creates and finally drops ONLY a generated phase5_*_test DB;
never alters the configured test DB or development DB. Logs stay in ignored tmp/.
"""
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url

ROOT=Path(__file__).resolve().parents[2]
BACKEND=ROOT/'backend'
TMP=ROOT/'tmp'


def main():
    assert Path(sys.prefix).resolve()==(BACKEND/'.venv').resolve(), 'Use backend/.venv'
    load_dotenv(BACKEND/'.env.local',override=True)
    base=make_url(os.environ['TEST_DATABASE_URL'])
    redis_url=os.environ['TEST_REDIS_URL']
    assert base.host in ('localhost','127.0.0.1') and base.database.endswith('_test')
    assert make_url(redis_url).database=='15', 'Only disposable Redis DB 15'
    name='phase5_'+uuid4().hex+'_test'
    assert re.fullmatch(r'phase5_[0-9a-f]{32}_test',name)
    url=base.set(database=name)
    env={**os.environ,'DATABASE_URL':url.render_as_string(hide_password=False),
         'REDIS_URL':redis_url,'APP_ENV':'production','JWT_SECRET':secrets.token_urlsafe(48),
         'BACKEND_CORS_ORIGINS':'["http://localhost:5173"]'}
    env.pop('ALEMBIC_TEST_SCHEMA',None)
    admin=create_engine(base.set(drivername='postgresql+psycopg2'),isolation_level='AUTOCOMMIT',hide_parameters=True)
    db=None; processes=[]; logs=[]; result={'database':name,'checks':{}}
    def record(key,value=True):
        result['checks'][key]=value
        print(key,':',value,flush=True)
    def start(label,code):
        log=(TMP/f'phase5-{label}.log').open('w',encoding='utf-8');logs.append(log)
        process=subprocess.Popen([sys.executable,'-c',code],cwd=BACKEND,env=env,
            stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        processes.append(process);return process
    def migration(*args):
        done=subprocess.run([sys.executable,'-m','alembic',*args],cwd=BACKEND,env=env,capture_output=True,text=True)
        with (TMP/'phase5-fresh-migrations.log').open('a',encoding='utf-8') as log:
            log.write(' '.join(args)+'\n'+done.stdout+done.stderr)
        assert done.returncode==0, 'Migration failed; inspect private migration log'
        return done.stdout
    try:
        with admin.connect() as conn: conn.execute(text(f'CREATE DATABASE "{name}"'))
        db=create_engine(url.set(drivername='postgresql+psycopg2'),hide_parameters=True)
        with db.begin() as conn: conn.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
        migration('upgrade','head');migration('check')
        record('fresh_upgrade_and_drift')
        # Seed only this newly-created database, using real models and password hashing.
        sys.path.insert(0,str(BACKEND))
        from sqlalchemy.orm import Session
        from app.models import User,Role,Permission,UserRole,RolePermission,Facility
        from app.security.auth import hasher
        password=secrets.token_urlsafe(24)
        with Session(db) as session,session.begin():
            user=User(username='readiness-worker',password_hash=hasher.hash(password),scope_mode='global')
            facility=Facility(code='READINESS-ONLY',name='Disposable readiness facility')
            role=Role(name='readiness-worker');session.add_all([user,facility,role]);session.flush()
            session.add(UserRole(user_id=user.id,role_id=role.id))
            for permission in session.scalars(__import__('sqlalchemy').select(Permission)):
                session.add(RolePermission(role_id=role.id,permission_id=permission.id))
            facility_id=str(facility.id)
        migration('downgrade','-1');migration('upgrade','head');migration('check')
        with db.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM facilities WHERE code='READINESS-ONLY'"))==1
            record('migration_head',conn.scalar(text('SELECT version_num FROM alembic_version')))
            record('postgis',conn.scalar(text('SELECT postgis_lib_version()')))
        record('downgrade_upgrade_preserves_record')
        import httpx
        import socket
        with socket.socket() as sock: sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        start('isolated-api',f"import uvicorn;uvicorn.run('app.main:app',host='127.0.0.1',port={port})")
        with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=10) as client:
            for _ in range(100):
                try:
                    if client.get('/api/v1/health').status_code==200:break
                except httpx.ConnectError:pass
                time.sleep(.2)
            assert client.get('/api/v1/users/me').status_code==401
            assert client.post('/api/v1/auth/login',data={'username':'readiness-worker','password':'wrong'}).status_code==401
            login=client.post('/api/v1/auth/login',data={'username':'readiness-worker','password':password});assert login.status_code==200
            tokens=login.json();client.headers['Authorization']='Bearer '+tokens['access_token']
            assert client.get('/api/v1/users/me').status_code==200
            refresh=client.post('/api/v1/auth/refresh',json={'refresh_token':tokens['refresh_token']});assert refresh.status_code==200
            client.headers['Authorization']='Bearer '+refresh.json()['data']['access_token']
            record('real_http_production_auth_refresh')
            payload={'facility_id':facility_id,'kind':'stock','format':'csv','idempotency_key':'queued-one'}
            first=client.post('/api/v1/report-jobs',json=payload);assert first.status_code==202
            assert client.post('/api/v1/report-jobs',json=payload).json()==first.json()
            identifier=first.json()['data']['id']
            queue='readiness-'+uuid4().hex
            boot="from app.tasks.celery_app import celery_app;celery_app.conf.task_default_queue="+repr(queue)+';'
            start('worker',boot+"celery_app.worker_main(['worker','--pool=solo','--concurrency=1','--loglevel=INFO','-Q',"+repr(queue)+",'--hostname=readiness@%h'])")
            from celery import Celery
            sender=Celery('readiness-probe',broker=redis_url,backend=redis_url)
            task=sender.send_task('reports.generate',queue=queue)
            assert task.get(timeout=60)==1
            assert client.get(f'/api/v1/report-jobs/{identifier}').json()['data']['status']=='completed'
            assert client.get(f'/api/v1/report-jobs/{identifier}/download').status_code==200
            retry=sender.send_task('reports.generate',queue=queue);assert retry.get(timeout=30)==0
            task.forget();retry.forget()
            record('queued_worker_generation_and_retry')
            second=client.post('/api/v1/report-jobs',json={**payload,'idempotency_key':'beat-two'});assert second.status_code==202
            second_id=second.json()['data']['id']
            schedule=str(TMP/('phase5-beat-'+uuid4().hex))
            start('beat',boot+"celery_app.conf.beat_schedule={'readiness':{'task':'reports.generate','schedule':1.0,'options':{'queue':"+repr(queue)+"}}};celery_app.start(['beat','--loglevel=INFO','--schedule',"+repr(schedule)+"])")
            for _ in range(100):
                if client.get(f'/api/v1/report-jobs/{second_id}').json()['data']['status']=='completed':break
                time.sleep(.2)
            assert client.get(f'/api/v1/report-jobs/{second_id}').json()['data']['status']=='completed'
            record('beat_publishes_worker_completes')
            assert client.post('/api/v1/auth/logout').status_code==200
            assert client.get('/api/v1/users/me').status_code==401
            record('logout_invalidates_access')
            record('production_startup_and_openapi',len(client.get('/api/v1/openapi.json').json()['paths']))
        result['passed']=True
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        for log in logs:log.close()
        if db:db.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        admin.dispose()
        result['temporary_processes_stopped']=all(p.poll() is not None for p in processes)
        result['owned_disposable_database_removed']=True
        (TMP/'phase5-worker.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
