from datetime import datetime,timezone,timedelta
import httpx
import pytest
from app.core.config import settings
from app.integrations.weather import fetch_weather
from tests.test_platform import seed,receipt
pytestmark=pytest.mark.asyncio


async def test_fhir_ai_barcode_recommendation_backup(api):
    client,_,_=api
    ids=await seed(client)
    batch=(await client.post('/api/v1/inventory/receive',json=receipt(ids))).json()['data']['batch_id']
    await client.post('/api/v1/inventory/issue',json={**ids,'quantity':2,'reference':'training'})
    fhir=(await client.get('/api/v1/integrations/fhir/locations/'+ids['facility_id'])).json()['data']
    assert fhir['resourceType']=='Location' and fhir['status']=='active'
    today=str(datetime.now(timezone.utc).date())
    consumption=await client.get('/api/v1/datasets/medicine-consumption',params={**ids,'start_date':today,'end_date':today})
    assert consumption.json()['data'][0]['consumed']==2
    barcode={'code':'BATCH-CODE-1','batch_id':batch}
    assert (await client.post('/api/v1/barcodes',json=barcode)).status_code==201
    assert (await client.post('/api/v1/barcodes',json=barcode)).status_code==409
    assert (await client.get('/api/v1/barcodes/lookup',params={'code':'BATCH-CODE-1'})).json()['data']['batch_id']==batch
    dest=(await client.post('/api/v1/facilities',json={'name':'Dest','code':'DEST'})).json()['data']['id']
    rec=await client.post('/api/v1/optimization/recommendations',json={'source_id':ids['facility_id'],'destination_id':dest,
        'model_version':'test-model','items':[{'batch_id':batch,'quantity':3}]})
    assert rec.status_code==201
    rid=rec.json()['data']['id']
    url=f'/api/v1/optimization/recommendations/{rid}/actions'
    assert (await client.post(url,json={'action':'apply'})).status_code==409
    assert (await client.post(url,json={'action':'approve'})).status_code==200
    applied=await client.post(url,json={'action':'apply'})
    assert applied.status_code==200
    transfer_id=applied.json()['data']['transfer_id']
    assert (await client.get(f'/api/v1/transfers/{transfer_id}')).json()['data']['status']=='pending_approval'
    assert (await client.get('/api/v1/inventory',params={'facility_id':ids['facility_id']})).json()['data'][0]['quantity']==8
    assert (await client.get('/api/v1/admin/backups/status')).json()['data']['healthy'] is False
    now=datetime.now(timezone.utc)
    backup={'artifact_key':'test-backup.dump','status':'completed','checksum':'a'*64,'size_bytes':10,
            'started_at':(now-timedelta(minutes=2)).isoformat(),'completed_at':(now-timedelta(minutes=1)).isoformat()}
    assert (await client.post('/api/v1/admin/backups',json=backup)).status_code==201
    assert (await client.get('/api/v1/admin/backups/status')).json()['data']['healthy'] is True


async def test_weather_validation_retry_and_failure(monkeypatch):
    monkeypatch.setattr(settings,'WEATHER_PROVIDER','open-meteo')
    attempts=[]
    def handler(request):
        attempts.append(request)
        if len(attempts)==1:
            return httpx.Response(503)
        return httpx.Response(200,json={'current':{'time':'2026-09-30T12:00','temperature_2m':25,'precipitation':0,'weather_code':1}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result=await fetch_weather(22.5,88.3,client)
        assert result['current']['temperature_2m']==25 and len(attempts)==2
    monkeypatch.setattr(settings,'WEATHER_PROVIDER',None)
    with pytest.raises(RuntimeError):
        await fetch_weather(22.5,88.3)


async def test_population_provenance(api):
    client,_,_=api
    parent=None
    for level in ('countries','states','districts'):
        parent=(await client.post('/api/v1/geography/'+level,json={'name':level,'code':level[:3],'parent_id':parent})).json()['data']['id']
    now=datetime.now(timezone.utc)
    payload={'district_id':parent,'population':1234,'source':'Test fixture only','source_url':'https://example.org/census',
             'as_of':str(now.date()),'retrieved_at':now.isoformat()}
    assert (await client.post('/api/v1/integrations/population',json=payload)).status_code==201
    assert (await client.get('/api/v1/integrations/population',params={'district_id':parent})).json()['data'][0]['population']==1234
