import pytest
from uuid import UUID
from sqlalchemy import select
from app.models import Inventory
from tests.test_platform import seed, receipt
pytestmark = pytest.mark.asyncio


async def prepare(client, quantity=6):
    ids = await seed(client)
    batch = (await client.post('/api/v1/inventory/receive', json=receipt(ids))).json()['data']['batch_id']
    destination = (await client.post('/api/v1/facilities', json={'name': 'Destination','code':'DEST'})).json()['data']['id']
    payload = {'source_id': ids['facility_id'],'destination_id':destination,'reference':'transfer-test',
               'items':[{'batch_id':batch,'quantity':quantity}],'idempotency_key':'transfer-1'}
    response = await client.post('/api/v1/transfers', json=payload)
    assert response.status_code == 201, response.text
    assert (await client.post('/api/v1/transfers', json=payload)).json() == response.json()
    return ids, destination, response.json()['data']['id']


async def test_transfer_full_workflow_reservation_receipt(api):
    client, _, _ = api
    ids, destination, identifier = await prepare(client)
    url = f'/api/v1/transfers/{identifier}/actions'
    assert (await client.post(url,json={'action':'receive','reason':'Too early'})).status_code == 409
    assert (await client.post(url,json={'action':'approve','reason':'Approved'})).status_code == 200
    assert (await client.post('/api/v1/inventory/issue',json={**ids,'quantity':5,'reference':'reserved'})).status_code == 409
    for action in ('dispatch','in_transit','receive'):
        response = await client.post(url,json={'action':action,'reason':action})
        assert response.status_code == 200, response.text
    assert (await client.post(url,json={'action':'receive','reason':'Duplicate'})).status_code == 409
    src = (await client.get('/api/v1/inventory',params={'facility_id':ids['facility_id']})).json()['data']
    dst = (await client.get('/api/v1/inventory',params={'facility_id':destination})).json()['data']
    assert src[0]['quantity'] == 4 and dst[0]['quantity'] == 6
    assert len((await client.get(f'/api/v1/transfers/{identifier}')).json()['data']['history']) == 5


async def test_transfer_insufficient_rejection(api):
    client, _, _ = api
    _, _, identifier = await prepare(client,11)
    url = f'/api/v1/transfers/{identifier}/actions'
    assert (await client.post(url,json={'action':'approve','reason':'Too much'})).status_code == 409
    assert (await client.post(url,json={'action':'reject','reason':'Insufficient'})).status_code == 200
    assert (await client.post(url,json={'action':'dispatch','reason':'Invalid'})).status_code == 409

async def test_transfer_cancel_releases_stock(api):
    client,_,_=api
    ids,_,identifier=await prepare(client)
    url=f'/api/v1/transfers/{identifier}/actions'
    assert (await client.post(url,json={'action':'approve','reason':'Reserve'})).status_code==200
    assert (await client.post(url,json={'action':'cancel','reason':'No longer needed'})).status_code==200
    response=await client.post('/api/v1/inventory/issue',json={**ids,'quantity':10,'reference':'released'})
    assert response.status_code==200


@pytest.mark.parametrize('deactivate_source', [True, False])
async def test_inactive_transfer_cancellation_releases_reservation(api, deactivate_source):
    client,factory,_=api
    ids,destination,identifier=await prepare(client)
    url=f'/api/v1/transfers/{identifier}/actions'
    assert (await client.post(url,json={'action':'approve','reason':'Reserve'})).status_code==200
    target=ids['facility_id'] if deactivate_source else destination
    assert (await client.patch('/api/v1/facilities/'+target,json={'active':False})).status_code==200
    assert (await client.post(url,json={'action':'dispatch','reason':'Blocked'})).status_code==409
    assert (await client.post(url,json={'action':'cancel','reason':'Recovery'})).status_code==200
    async with factory() as db:
        row=await db.scalar(select(Inventory).where(Inventory.facility_id==UUID(ids['facility_id'])))
        assert row.reserved==0 and row.quantity==10
    for action in ('cancel','approve','receive'):
        assert (await client.post(url,json={'action':action,'reason':'Invalid repeat'})).status_code==409


@pytest.mark.parametrize('deactivate_source', [True, False])
async def test_inactive_transfer_receipt_recovery(api, deactivate_source):
    client,_,_=api
    ids,destination,identifier=await prepare(client)
    url=f'/api/v1/transfers/{identifier}/actions'
    for action in ('approve','dispatch'):
        assert (await client.post(url,json={'action':action,'reason':action})).status_code==200
    target=ids['facility_id'] if deactivate_source else destination
    await client.patch('/api/v1/facilities/'+target,json={'active':False})
    assert (await client.post(url,json={'action':'receive','reason':'Recover goods'})).status_code==200
    assert (await client.post(url,json={'action':'receive','reason':'Duplicate'})).status_code==409
    stock=(await client.get('/api/v1/inventory',params={'facility_id':destination})).json()['data']
    assert stock[0]['quantity']==6
