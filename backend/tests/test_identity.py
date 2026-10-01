from uuid import UUID
import pytest
from sqlalchemy import select
from app.models import User, Role, UserRole
from app.models.identity import AuthSession, PasswordReset, UserFacility
from app.security.auth import access_token
from app.integrations import identity as adapters
from tests.test_platform import seed

pytestmark = pytest.mark.asyncio


async def login(client):
    response = await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password'})
    assert response.status_code == 200
    return response.json()


async def test_rotation_replay_revokes_family(api):
    client, factory, _ = api
    first = await login(client)
    rotated = await client.post('/api/v1/auth/refresh', json={'refresh_token': first['refresh_token']})
    assert rotated.status_code == 200
    second = rotated.json()['data']
    assert first['refresh_token'] != second['refresh_token']
    replay = await client.post('/api/v1/auth/refresh', json={'refresh_token': first['refresh_token']})
    assert replay.status_code == 401
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': second['refresh_token']})).status_code == 401
    client.headers['Authorization'] = 'Bearer ' + second['access_token']
    assert (await client.get('/api/v1/users/me')).status_code == 401
    async with factory() as db:
        stored = await db.scalar(select(AuthSession))
        assert stored.revoked and stored.token_hash != second['refresh_token']


async def test_logout_and_password_change(api):
    client, _, _ = api
    tokens = await login(client)
    client.headers['Authorization'] = 'Bearer ' + tokens['access_token']
    assert (await client.post('/api/v1/auth/logout')).status_code == 200
    assert (await client.get('/api/v1/users/me')).status_code == 401
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']})).status_code == 401
    tokens = await login(client)
    client.headers['Authorization'] = 'Bearer ' + tokens['access_token']
    response = await client.post('/api/v1/auth/password/change', json={'current_password': 'correct-password', 'new_password': 'new-secure-password'})
    assert response.status_code == 200
    assert (await client.get('/api/v1/users/me')).status_code == 401
    assert (await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password'})).status_code == 401


async def test_reset_single_use_and_no_token_disclosure(api, monkeypatch):
    client, factory, _ = api
    class Delivery:
        async def deliver(self, user_id, token):
            self.token = token
    delivery = Delivery()
    monkeypatch.setattr(adapters, 'reset_delivery', delivery)
    known = await client.post('/api/v1/auth/password/reset/request', json={'username': 'admin'})
    unknown = await client.post('/api/v1/auth/password/reset/request', json={'username': 'missing'})
    assert known.json() == unknown.json()
    assert delivery.token not in known.text
    async with factory() as db:
        reset = await db.scalar(select(PasswordReset))
        assert reset.token_hash != delivery.token
    payload = {'token': delivery.token, 'new_password': 'new-reset-password'}
    assert (await client.post('/api/v1/auth/password/reset/confirm', json=payload)).status_code == 200
    assert (await client.post('/api/v1/auth/password/reset/confirm', json=payload)).status_code == 400


async def test_user_admin_scoping_and_mass_assignment(api):
    client, factory, reader = api
    ids = await seed(client)
    response = await client.post('/api/v1/users', json={'username': 'scoped', 'password': 'long-safe-password'})
    assert response.status_code == 201
    assert 'password_hash' not in response.text
    identifier = response.json()['data']['id']
    roles = (await client.get('/api/v1/roles')).json()['data']
    assert (await client.put(f'/api/v1/users/{identifier}/roles/{roles[0]["id"]}')).status_code == 200
    assert (await client.put(f'/api/v1/users/{identifier}/facilities/{ids["facility_id"]}')).status_code == 200
    token = (await client.post('/api/v1/auth/login', data={'username': 'scoped', 'password': 'long-safe-password'})).json()['access_token']
    client.headers['Authorization'] = 'Bearer ' + token
    assert len((await client.get('/api/v1/facilities')).json()['data']) == 1
    assert (await client.get('/api/v1/users')).status_code == 403
    assert (await client.get('/api/v1/inventory', params={'facility_id': str(reader)})).status_code == 404
    assert (await client.patch(f'/api/v1/users/{identifier}', json={'password_hash': 'bypass'})).status_code in (403, 422)


async def test_mfa_hook_fails_closed(api):
    client, factory, _ = api
    async with factory.begin() as db:
        user = await db.scalar(select(User).where(User.username == 'admin'))
        user.mfa_required = True
    assert (await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password'})).status_code == 401

async def test_recovery_provider_failure_is_private(api,monkeypatch):
    client,factory,_=api
    class Unavailable:
        async def deliver(self,user_id,token):
            raise RuntimeError('private-provider-detail')
    monkeypatch.setattr(adapters,'reset_delivery',Unavailable())
    known=await client.post('/api/v1/auth/password/reset/request',json={'username':'admin'})
    unknown=await client.post('/api/v1/auth/password/reset/request',json={'username':'not-an-account'})
    assert known.status_code==unknown.status_code==202
    assert known.json()==unknown.json()
    assert 'private-provider-detail' not in known.text
    async with factory() as db:
        reset=await db.scalar(select(PasswordReset))
        assert reset.used is True


async def test_mfa_provider_success_and_failure(api,monkeypatch):
    client,factory,_=api
    async with factory.begin() as db:
        user=await db.scalar(select(User).where(User.username=='admin'))
        user.mfa_required=True
    class Verifier:
        async def verify(self,user_id,proof):
            return proof=='test-proof'
    monkeypatch.setattr(adapters,'mfa_verifier',Verifier())
    response=await client.post('/api/v1/auth/login',data={'username':'admin','password':'correct-password','mfa_proof':'test-proof'})
    assert response.status_code==200
    response=await client.post('/api/v1/auth/login',data={'username':'admin','password':'correct-password','mfa_proof':'wrong'})
    assert response.status_code==401
