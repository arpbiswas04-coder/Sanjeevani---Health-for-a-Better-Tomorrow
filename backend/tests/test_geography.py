import pytest
from tests.test_platform import seed
pytestmark = pytest.mark.asyncio


async def test_geography_facility_filters_nearby(api):
    client, _, _ = api
    ids = await seed(client)
    parent = None
    for level, code in [('countries','IN'),('states','WB'),('districts','D1'),('blocks','B1')]:
        response = await client.post('/api/v1/geography/' + level, json={'name': code, 'code': code, 'parent_id': parent})
        assert response.status_code == 201, response.text
        parent = response.json()['data']['id']
    response = await client.patch('/api/v1/facilities/' + ids['facility_id'], json={'block_id': parent, 'latitude': 22.5, 'longitude': 88.3, 'address': 'Test address'})
    assert response.status_code == 200
    assert response.json()['data']['version'] == 2
    assert len((await client.get('/api/v1/facilities', params={'block_id': parent})).json()['data']) == 1
    nearby = await client.get('/api/v1/facilities/nearby', params={'latitude': 22.5, 'longitude': 88.3})
    assert nearby.status_code == 200, nearby.text
    assert nearby.json()['data'][0]['distance_km'] == 0
    assert (await client.patch('/api/v1/facilities/' + ids['facility_id'], json={'latitude': 0})).status_code == 422
    await client.patch('/api/v1/facilities/' + ids['facility_id'], json={'active': False})
    assert (await client.get('/api/v1/facilities')).json()['data'] == []
    assert (await client.get('/api/v1/facilities/' + ids['facility_id'])).status_code == 200
