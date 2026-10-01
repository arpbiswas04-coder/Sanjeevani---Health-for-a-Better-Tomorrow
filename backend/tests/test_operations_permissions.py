from uuid import UUID
import pytest
from sqlalchemy import select
from app.models import User,Role,Permission,UserRole,RolePermission
from app.models.identity import UserFacility
from app.security.auth import access_token
from tests.test_platform import seed

pytestmark=pytest.mark.asyncio


async def grant(factory, user_id, facility_id, permissions):
    async with factory.begin() as db:
        role=Role(name='narrow-reader')
        db.add(role)
        await db.flush()
        db.add(UserRole(user_id=user_id,role_id=role.id))
        db.add(UserFacility(user_id=user_id,facility_id=UUID(facility_id)))
        for name in permissions:
            permission=await db.scalar(select(Permission).where(Permission.name==name))
            db.add(RolePermission(role_id=role.id,permission_id=permission.id))


@pytest.mark.parametrize('permission,allowed,denied',[
    ('beds.read',['beds'],['staff','footfall','temperatures']),
    ('workforce.read',['staff','shifts','attendance'],['beds','footfall']),
    ('integration.read',['footfall','disease-counts'],['beds','staff']),
])
async def test_narrow_operational_reader(api,permission,allowed,denied):
    client,factory,reader=api
    ids=await seed(client)
    other=(await client.post('/api/v1/facilities',json={'name':'Other','code':'OTHER'})).json()['data']['id']
    await grant(factory,reader,ids['facility_id'],[permission])
    client.headers['Authorization']='Bearer '+access_token(reader)
    for kind in allowed:
        assert (await client.get('/api/v1/operations/'+kind,params={'facility_id':ids['facility_id']})).status_code==200
        assert (await client.get('/api/v1/operations/'+kind,params={'facility_id':other})).status_code==404
    for kind in denied:
        assert (await client.get('/api/v1/operations/'+kind,params={'facility_id':ids['facility_id']})).status_code==403
