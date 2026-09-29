import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models import User, Role, Permission, RolePermission, UserRole
from app.security.auth import hasher, access_token


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'JWT_SECRET', 'test-only-secret-that-is-at-least-32-characters')
    engine = create_async_engine('sqlite+aiosqlite:///' + str(tmp_path / 'test.db'))
    @event.listens_for(engine.sync_engine, 'connect')
    def enable_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        admin = User(username='admin', password_hash=hasher.hash('correct-password'))
        reader = User(username='reader', password_hash=hasher.hash('reader-password'))
        role = Role(name='admin')
        db.add_all([admin, reader, role])
        await db.flush()
        db.add(UserRole(user_id=admin.id, role_id=role.id))
        for name in ('inventory.read', 'inventory.write', 'facility.manage'):
            permission = Permission(name=name)
            db.add(permission)
            await db.flush()
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    async def database():
        async with factory() as db:
            async with db.begin():
                yield db
    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        client.headers['Authorization'] = 'Bearer ' + access_token(admin.id)
        yield client, factory, reader.id
    app.dependency_overrides.clear()
    await engine.dispose()
