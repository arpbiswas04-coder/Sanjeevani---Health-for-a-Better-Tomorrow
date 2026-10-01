import pytest
from app.core.config import settings
from app.security import rate_limit
pytestmark=pytest.mark.asyncio


async def test_auth_rate_limit_and_production_fail_closed(api,monkeypatch):
    client,_,_=api
    monkeypatch.setattr(settings,'APP_ENV','development')
    monkeypatch.setattr(settings,'AUTH_RATE_LIMIT',1)
    rate_limit._local.clear()
    body={'username':'nonexistent','password':'wrong'}
    assert (await client.post('/api/v1/auth/login',data=body)).status_code==401
    response=await client.post('/api/v1/auth/login',data=body)
    assert response.status_code==429 and 'Retry-After' in response.headers
    monkeypatch.setattr(settings,'APP_ENV','production')
    monkeypatch.setattr(settings,'REDIS_URL',None)
    response=await client.post('/api/v1/auth/login',data=body)
    assert response.status_code==503
    rate_limit._local.clear()


async def test_secret_fields_not_in_admin_configuration(api):
    client,_,_=api
    response=await client.get('/api/v1/admin/config')
    assert response.status_code==200
    for value in ('JWT_SECRET','DATABASE_URL','POSTGRES_PASSWORD','password_hash','token_hash'):
        assert value not in response.text

async def test_application_lifespan_and_openapi(api):
    from app.main import app
    async with app.router.lifespan_context(app):
        schema=app.openapi()
        assert '/api/v1/report-jobs' in schema['paths']
        assert '/api/v1/auth/refresh' in schema['paths']
        assert '/api/v1/sync/push' in schema['paths']
