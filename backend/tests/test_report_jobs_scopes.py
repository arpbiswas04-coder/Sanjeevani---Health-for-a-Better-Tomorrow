from datetime import datetime,timezone,timedelta
from uuid import UUID
import pytest
from sqlalchemy import select
from app.models import User
from app.models.identity import UserDistrict
from app.models.report_jobs import ReportJob
from app.services.report_jobs import due_schedules,generate_pending,expire_artifacts
from tests.test_platform import seed
pytestmark=pytest.mark.asyncio


async def test_background_reports_and_schedules(api):
    client,factory,_=api
    ids=await seed(client)
    payload={'facility_id':ids['facility_id'],'kind':'beds','format':'csv'}
    job=await client.post('/api/v1/report-jobs',json=payload)
    assert job.status_code==202
    jid=job.json()['data']['id']
    assert 'content' not in job.json()['data']
    assert (await client.get(f'/api/v1/report-jobs/{jid}/download')).status_code==409
    async with factory.begin() as db:
        assert await generate_pending(db)==1
    assert (await client.get(f'/api/v1/report-jobs/{jid}/download')).status_code==200
    schedule=await client.post('/api/v1/report-schedules',json={**payload,'interval_minutes':30})
    assert schedule.status_code==201
    async with factory.begin() as db:
        assert await due_schedules(db)==1
    async with factory.begin() as db:
        assert await due_schedules(db)==0
    assert (await client.delete('/api/v1/report-schedules/'+schedule.json()['data']['id'])).status_code==200
    async with factory.begin() as db:
        row=await db.get(ReportJob,UUID(jid))
        row.expires_at=datetime.now(timezone.utc)-timedelta(minutes=1)
    assert (await client.get(f'/api/v1/report-jobs/{jid}/download')).status_code==409
    async with factory.begin() as db:
        assert await expire_artifacts(db)==1
        row=await db.get(ReportJob,UUID(jid))
        assert row.content is None and row.status=='expired'


async def test_regional_scope_is_dynamic(api):
    client,factory,_=api
    ids=await seed(client)
    parent=None
    district=None
    for kind in ('countries','states','districts','blocks'):
        parent=(await client.post('/api/v1/geography/'+kind,json={'name':kind,'code':kind[:3],'parent_id':parent})).json()['data']['id']
        if kind=='districts':district=parent
    await client.patch('/api/v1/facilities/'+ids['facility_id'],json={'block_id':parent})
    async with factory.begin() as db:
        user=await db.scalar(select(User).where(User.username=='admin'))
        user.scope_mode='restricted'
        db.add(UserDistrict(user_id=user.id,district_id=UUID(district)))
    response=await client.get('/api/v1/facilities')
    assert response.status_code==200 and len(response.json()['data'])==1

async def test_worker_execution_uses_isolated_database(api,monkeypatch):
    import asyncio
    from app.core.config import settings
    from app.tasks.jobs import generate_reports
    client,factory,_=api
    ids=await seed(client)
    monkeypatch.setattr(settings,'DATABASE_URL',factory.kw['bind'].url.render_as_string(hide_password=False))
    response=await client.post('/api/v1/report-jobs',json={'facility_id':ids['facility_id'],'kind':'beds','format':'csv'})
    assert response.status_code==202
    assert await asyncio.to_thread(generate_reports.run)==1
    assert (await client.get('/api/v1/report-jobs/'+response.json()['data']['id'])).json()['data']['status']=='completed'
