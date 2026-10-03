"""Opt-in checks against disposable PostgreSQL and Redis, never development data."""
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from redis.asyncio import Redis
from tests.test_postgres import pg, TEST_URL
from app.core.config import settings
from app.core.database import get_db
from app.main import app

pytestmark = pytest.mark.asyncio
requires_pg = pytest.mark.skipif(not TEST_URL, reason='Disposable TEST_DATABASE_URL not configured')


@requires_pg
async def test_extension_filter_preserves_real_drift(pg):
    factory, _, _, _ = pg
    schema = factory.kw['bind'].get_execution_options()['schema_translate_map'][None]
    async def check():
        return await asyncio.to_thread(subprocess.run,
            [sys.executable, '-m', 'alembic', 'check'], cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, 'DATABASE_URL': TEST_URL, 'ALEMBIC_TEST_SCHEMA': schema},
            capture_output=True, text=True)
    clean = await check()
    assert clean.returncode == 0, clean.stdout + clean.stderr
    async with factory.begin() as db:
        await db.execute(text(f'ALTER TABLE "{schema}".users ADD COLUMN phase2_drift_probe integer'))
        await db.execute(text(f'CREATE TABLE "{schema}".phase2_unmanaged_probe (id integer)'))
        # An application table with an extension table's name must not be hidden.
        await db.execute(text(f'CREATE TABLE "{schema}".spatial_ref_sys (id integer)'))
    drift = await check()
    assert drift.returncode != 0
    output = drift.stdout + drift.stderr
    assert 'phase2_drift_probe' in output and 'phase2_unmanaged_probe' in output
    assert "Detected removed table 'spatial_ref_sys'" in output


@requires_pg
async def test_postgres_authentication_and_facility_permissions(pg, monkeypatch):
    from app.models import User, Role, Permission, UserRole, RolePermission, Facility
    from app.models.identity import UserFacility
    from app.security.auth import hasher
    from sqlalchemy import select
    factory, user, assigned, _ = pg
    monkeypatch.setattr(settings, 'APP_ENV', 'testing')
    monkeypatch.setattr(settings, 'JWT_SECRET', 'isolated-infrastructure-test-secret-32-characters')
    async with factory.begin() as db:
        stored = await db.get(User, user.id)
        stored.scope_mode = 'restricted'
        stored.password_hash = hasher.hash('isolated-test-password')
        role = Role(name='facility_admin')
        other = Facility(name='Other', code='OTHER', latitude=22.6, longitude=88.4)
        db.add_all([role, other])
        await db.flush()
        permission = await db.scalar(select(Permission).where(Permission.name == 'inventory.read'))
        db.add_all([UserRole(user_id=user.id, role_id=role.id),
                    RolePermission(role_id=role.id, permission_id=permission.id),
                    UserFacility(user_id=user.id, facility_id=assigned.id)])
    async def database():
        async with factory.begin() as db:
            yield db
    app.dependency_overrides[get_db] = database
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.post('/api/v1/auth/login', data={'username': 'tester', 'password': 'wrong'})).status_code == 401
            login = await client.post('/api/v1/auth/login', data={'username': 'tester', 'password': 'isolated-test-password'})
            assert login.status_code == 200
            tokens = login.json()
            client.headers['Authorization'] = 'Bearer ' + tokens['access_token']
            profile = (await client.get('/api/v1/users/me')).json()['data']
            assert profile['roles'] == ['facility_admin'] and profile['permissions'] == ['inventory.read']
            assert profile['facility_ids'] == [str(assigned.id)]
            facilities = (await client.get('/api/v1/facilities')).json()['data']
            assert [f['id'] for f in facilities] == [str(assigned.id)]
            assert (await client.get('/api/v1/inventory', params={'facility_id': str(assigned.id)})).status_code == 200
            assert (await client.get('/api/v1/inventory', params={'facility_id': str(other.id)})).status_code in (403, 404)
            assert (await client.get('/api/v1/users', headers={'X-Role': 'SUPER_ADMIN'})).status_code == 403
            refreshed = await client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']})
            assert refreshed.status_code == 200
            rotated = refreshed.json()['data']
            assert rotated['refresh_token'] != tokens['refresh_token']
            client.headers['Authorization'] = 'Bearer ' + rotated['access_token']
            assert (await client.get('/api/v1/users/me')).status_code == 200
            assert (await client.post('/api/v1/auth/logout')).status_code == 200
            assert (await client.get('/api/v1/users/me')).status_code == 401
            assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': rotated['refresh_token']})).status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.skipif(not os.environ.get('TEST_REDIS_URL'), reason='Disposable TEST_REDIS_URL not configured')
async def test_real_redis_rate_limit_and_dependency_failure(api, monkeypatch):
    from app.security import rate_limit
    from urllib.parse import urlparse
    url = os.environ['TEST_REDIS_URL']
    assert urlparse(url).path == '/15', 'Only disposable Redis database 15 is permitted'
    monkeypatch.setattr(settings, 'APP_ENV', 'production')
    monkeypatch.setattr(settings, 'REDIS_URL', url)
    monkeypatch.setattr(settings, 'AUTH_RATE_LIMIT', 1)
    key = 'phase2-' + uuid4().hex
    async with Redis.from_url(url) as redis:
        assert await redis.ping()
        try:
            assert await rate_limit.allowed(key) is True
            assert await rate_limit.allowed(key) is False
            assert await redis.ttl('auth-limit:' + key) > 0
        finally:
            await redis.delete('auth-limit:' + key)
    # An invalid database index on the actual server forces a real Redis error,
    # without stopping shared services or changing development data.
    monkeypatch.setattr(settings, 'REDIS_URL', url.rsplit('/', 1)[0] + '/999999')
    client, _, _ = api
    body = {'username': 'admin', 'password': 'correct-password'}
    result = await client.post('/api/v1/auth/login', data=body)
    assert result.status_code == 503 and result.json()['error']['code'] == 'AUTH_UNAVAILABLE'
    monkeypatch.setattr(settings, 'APP_ENV', 'development')
    rate_limit._local.clear()
    assert (await client.post('/api/v1/auth/login', data=body)).status_code == 200
    rate_limit._local.clear()
