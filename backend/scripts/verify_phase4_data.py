"""Development-only live UI fixture and independent SQL probes. Never resets data.

Run from backend with .venv Python: prepare | inspect FACILITY_ID | generate JOB_ID.
The manifest is ignored, contains no credentials, and identifies only this run's records.
"""
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
import httpx
from sqlalchemy import select, text, func
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.models import Facility, Inventory, StockTransaction, AuditLog, User
from app.models.operations import BedCapacity
from app.models.alerts import Alert
from app.models.transfers import TransferRequest
from app.models.report_jobs import ReportJob
from app.services.alerts import evaluate_rule
from app.services.report_jobs import generate_pending

MANIFEST=ROOT/'tmp/phase4-fixture.json'

async def guard(db):
    url=make_url(settings.get_database_url())
    assert settings.APP_ENV=='development' and url.database=='sanjeevani_dev' and url.host in ('localhost','127.0.0.1')
    assert await db.scalar(text('SELECT current_database()'))=='sanjeevani_dev'

async def prepare():
    assert not MANIFEST.exists(), 'Existing Phase 4 manifest retained; use its existing records or explicitly archive it before a new isolated run.'
    async with AsyncSessionLocal() as db:
        await guard(db)
    credentials=json.loads((ROOT/'tmp/phase2-auth-account.json').read_text())
    run='DEV-P4-'+uuid4().hex[:8]
    async with httpx.AsyncClient(base_url='http://localhost:8000',timeout=20) as client:
        response=await client.post('/api/v1/auth/login',data=credentials)
        assert response.status_code==200,'Real administrator login failed'
        client.headers['Authorization']='Bearer '+response.json()['access_token']
        me=(await client.get('/api/v1/users/me')).json()['data']
        assert me['scope_mode']=='global'
        async with AsyncSessionLocal() as db:
            assert await db.get(User,UUID(me['id'])) is not None
        async def create(path,body):
            response=await client.post('/api/v1'+path,json=body)
            assert response.status_code<300, f'{path} returned {response.status_code}'
            return response.json()['data']
        medicine=await create('/medicines',{'code':run,'name':'DEVELOPMENT ONLY Phase 4 medicine '+run,'unit':'test-unit'})
        manifest={'database':'sanjeevani_dev','run':run,'medicine_id':medicine['id'],'medicine_name':medicine['name'],'facilities':{}}
        # Persist each created identifier so interrupted preparation never loses ownership.
        MANIFEST.write_text(json.dumps(manifest,indent=2))
        for kind in ['inventory','transfer','destination','alerts','operations','reports']:
            facility=await create('/facilities',{'code':run+'-'+kind[:4],'name':'DEVELOPMENT ONLY Phase 4 '+kind+' '+run})
            manifest['facilities'][kind]={'id':facility['id'],'name':facility['name']}
            MANIFEST.write_text(json.dumps(manifest,indent=2))
            if kind!='destination':
                receipt=await create('/inventory/receive',{'facility_id':facility['id'],'medicine_id':medicine['id'],
                    'batch_number':run,'expires_on':str(datetime.now(timezone.utc).date()+timedelta(days=90)),
                    'quantity':20,'reference':run+' setup','idempotency_key':run+'-'+kind})
                manifest['facilities'][kind].update(receipt)
                manifest['batch_id']=receipt['batch_id']
            if kind=='operations':
                result=await client.put('/api/v1/beds',json={'facility_id':facility['id'],'bed_type':run,'capacity':10,'occupied':2})
                assert result.status_code==200
            if kind=='alerts':
                rule=await create('/alert-rules',{'facility_id':facility['id'],'kind':'LOW_STOCK','threshold':100,'severity':'warning'})
                async with AsyncSessionLocal.begin() as db:
                    await guard(db)
                    assert await evaluate_rule(db,UUID(rule['id']))==1
                manifest['rule_id']=rule['id']
            MANIFEST.write_text(json.dumps(manifest,indent=2))
    print('Prepared isolated Phase 4 records; manifest: tmp/phase4-fixture.json')

async def inspect(identifier):
    manifest=json.loads(MANIFEST.read_text()); ids={v['id'] for v in manifest['facilities'].values()}
    assert identifier in ids
    async with AsyncSessionLocal() as db:
        await guard(db)
        facility=await db.get(Facility,UUID(identifier)); assert facility.code.startswith(manifest['run'])
        quantity=await db.scalar(select(func.coalesce(func.sum(Inventory.quantity),0)).where(Inventory.facility_id==facility.id))
        ledger=await db.scalar(select(func.count()).select_from(StockTransaction).join(Inventory).where(Inventory.facility_id==facility.id))
        beds=[{'capacity':r.capacity,'occupied':r.occupied} for r in await db.scalars(select(BedCapacity).where(BedCapacity.facility_id==facility.id))]
        alerts=[{'id':str(r.id),'status':r.status} for r in await db.scalars(select(Alert).where(Alert.facility_id==facility.id))]
        transfers=[{'id':str(r.id),'status':r.status} for r in await db.scalars(select(TransferRequest).where(TransferRequest.source_id==facility.id))]
        jobs=[{'id':str(r.id),'status':r.status,'bytes':len(r.content or b'')} for r in await db.scalars(select(ReportJob).where(ReportJob.facility_id==facility.id))]
        print(json.dumps({'quantity':quantity,'ledger_count':ledger,'beds':beds,'alerts':alerts,'transfers':transfers,'jobs':jobs}))

async def generate(identifier):
    manifest=json.loads(MANIFEST.read_text())
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        # Prevent concurrent new report inserts while selecting exactly this owned job.
        await db.execute(text('LOCK TABLE report_jobs IN SHARE ROW EXCLUSIVE MODE'))
        pending=list(await db.scalars(select(ReportJob).where(ReportJob.status=='pending')))
        assert len(pending)==1 and str(pending[0].id)==identifier, 'Refusing to process unrelated or multiple pending jobs'
        assert str(pending[0].facility_id)==manifest['facilities']['reports']['id']
        assert await generate_pending(db)==1
    print('Generated the isolated report through the existing report service; no worker/beat claim.')

async def rearm_alert(identifier):
    manifest=json.loads(MANIFEST.read_text())
    assert identifier==manifest['facilities']['alerts']['id']
    from app.models.alerts import AlertRule
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        rule=await db.get(AlertRule,UUID(manifest['rule_id']))
        assert str(rule.facility_id)==identifier
        await evaluate_rule(db,rule.id)
    print('Evaluated only the isolated development alert rule.')

async def restore_bed(identifier):
    manifest=json.loads(MANIFEST.read_text())
    assert identifier==manifest['facilities']['operations']['id']
    from app.schemas.operations import BedInput
    from app.services.operations import bed_update
    credentials=json.loads((ROOT/'tmp/phase2-auth-account.json').read_text())
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        facility=await db.get(Facility,UUID(identifier)); assert facility.code.startswith(manifest['run'])
        user=await db.scalar(select(User).where(User.username==credentials['username']))
        await bed_update(db,user,BedInput(facility_id=facility.id,bed_type=manifest['run'],capacity=10,occupied=2))
    print('Restored only the isolated Phase 4 bed fixture to its seeded values.')

async def main():
    try:
        if sys.argv[1]=='prepare': await prepare()
        elif sys.argv[1]=='inspect': await inspect(sys.argv[2])
        elif sys.argv[1]=='generate': await generate(sys.argv[2])
        elif sys.argv[1]=='alert': await rearm_alert(sys.argv[2])
        elif sys.argv[1]=='restore-bed': await restore_bed(sys.argv[2])
        else: raise ValueError('Unknown command')
    finally: await engine.dispose()

if __name__=='__main__': asyncio.run(main())
