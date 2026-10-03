from datetime import datetime, timedelta, timezone
import jwt
import pytest
from sqlalchemy import delete
from sqlalchemy.exc import OperationalError
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import UserRole
from app.security.auth import access_token

pytestmark = pytest.mark.asyncio


async def test_form_contract_and_authoritative_profile(api):
    client, factory, reader = api
    assert (await client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'correct-password'})).status_code == 422
    login = await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password', 'grant_type': 'password'})
    assert login.status_code == 200
    tokens = login.json()
    assert set(tokens) == {'access_token', 'refresh_token', 'token_type', 'expires_in'}
    claims = jwt.decode(tokens['access_token'], settings.JWT_SECRET, algorithms=['HS256'], issuer='sanjeevani')
    assert claims['type'] == 'access' and claims['sid']
    client.headers['Authorization'] = 'Bearer ' + tokens['access_token']
    me = (await client.get('/api/v1/users/me')).json()['data']
    assert me['username'] == 'admin' and me['roles'] == ['admin']
    assert 'admin.users' in me['permissions']
    assert me['facility_ids'] == me['district_ids'] == []
    assert not {'password_hash', 'token_version'} & set(me)
    assert (await client.get('/api/v1/users')).status_code == 200
    # Removing grants takes effect with the same valid JWT; no role claim is trusted.
    from uuid import UUID
    async with factory.begin() as db:
        await db.execute(delete(UserRole).where(UserRole.user_id == UUID(me['id'])))
    assert (await client.get('/api/v1/users/me')).json()['data']['permissions'] == []
    assert (await client.get('/api/v1/users')).status_code == 403


async def test_incorrect_demo_credentials_expiry_and_logout(api):
    client, _, reader = api
    for username, password in [('admin', 'wrong'), ('national.command@sanjeevani.gov.in', 'NationalPass2026!')]:
        assert (await client.post('/api/v1/auth/login', data={'username': username, 'password': password})).status_code == 401
    client.headers['Authorization'] = 'Bearer sg_jwt_super_admin_123'
    assert (await client.get('/api/v1/users/me')).status_code == 401
    now = datetime.now(timezone.utc)
    expired = jwt.encode({'sub': str(reader), 'iat': now - timedelta(hours=1), 'exp': now - timedelta(seconds=1),
                          'type': 'access', 'iss': 'sanjeevani', 'role': 'SUPER_ADMIN'}, settings.JWT_SECRET, algorithm='HS256')
    client.headers['Authorization'] = 'Bearer ' + expired
    assert (await client.get('/api/v1/users/me')).status_code == 401
    client.headers['Authorization'] = 'Bearer ' + access_token(reader)
    assert (await client.get('/api/v1/users/me')).json()['data']['permissions'] == []
    assert (await client.get('/api/v1/users', headers={'X-Role': 'SUPER_ADMIN'})).status_code == 403
    tokens = (await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password'})).json()
    refreshed = await client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']})
    assert refreshed.status_code == 200
    tokens = refreshed.json()['data']
    client.headers['Authorization'] = 'Bearer ' + tokens['access_token']
    assert (await client.post('/api/v1/auth/logout')).status_code == 200
    assert (await client.get('/api/v1/users/me')).status_code == 401
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']})).status_code == 401


async def test_database_dependency_unavailable_is_sanitized(api, monkeypatch):
    client, _, _ = api
    from app.core import database
    class Unavailable:
        async def __aenter__(self):
            raise OperationalError('private-sql', {}, RuntimeError('private-connection-secret'))
        async def __aexit__(self, *args):
            pass
    monkeypatch.setattr(database, 'AsyncSessionLocal', Unavailable)
    override = app.dependency_overrides.pop(get_db)
    try:
        result = await client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'correct-password'})
        assert result.status_code == 503
        assert result.json()['error']['code'] == 'SERVICE_UNAVAILABLE'
        assert 'Database unavailable' in result.text and 'private-' not in result.text
    finally:
        app.dependency_overrides[get_db] = override


async def test_openapi_profile_and_cors(api):
    client, _, _ = api
    schema = (await client.get('/api/v1/openapi.json')).json()
    assert 'application/x-www-form-urlencoded' in schema['paths']['/api/v1/auth/login']['post']['requestBody']['content']
    assert {'roles', 'permissions', 'facility_ids', 'district_ids'} <= set(schema['components']['schemas']['CurrentUserView']['required'])
    preflight = await client.options('/api/v1/users/me', headers={'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'authorization'})
    assert preflight.status_code == 200
    assert preflight.headers['access-control-allow-origin'] == 'http://localhost:5173'
