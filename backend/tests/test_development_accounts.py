import json
from uuid import UUID

import pytest
from sqlalchemy import select, func
from app.models import User, UserRole, Facility, Medicine
from app.security.auth import hasher
from scripts.development_accounts import passwords, provision_matrix, identity_snapshot
from scripts.development_seed import PROFILES, create_user, seed_operations


def test_password_sources_are_explicit_and_never_return_secrets_in_labels(monkeypatch, tmp_path):
    monkeypatch.delenv('SANJEEVANI_DEV_TEST_PASSWORD', raising=False)
    with pytest.raises(ValueError, match='Supply'):
        passwords()
    file = tmp_path / 'private.json'
    file.write_text(json.dumps({key: {'username': 'dev-data-' + key, 'password': 'isolated-matrix-password'} for key in PROFILES}))
    sources = passwords(file)
    assert all('password' in source and 'isolated' not in source for _, source in sources.values())
    monkeypatch.setenv('SANJEEVANI_DEV_TEST_PASSWORD', 'shared-isolated-password')
    assert all(value == ('shared-isolated-password', 'SANJEEVANI_DEV_TEST_PASSWORD') for value in passwords(file).values())
    monkeypatch.delenv('SANJEEVANI_DEV_TEST_PASSWORD')
    file.write_text(json.dumps({'admin': {'username': 'arpan', 'password': 'isolated-matrix-password'}}))
    with pytest.raises(ValueError, match='owned'):
        passwords(file)


@pytest.mark.asyncio
async def test_account_matrix_reuses_all_real_profiles_without_changing_arpan(api):
    client, factory, _ = api
    secret = 'isolated-matrix-password'
    sources = {key: (secret, 'SANJEEVANI_DEV_TEST_PASSWORD') for key in PROFILES}
    async with factory.begin() as db:
        administrator = await create_user(db, 'admin', secret, [])
        arpan = User(username='arpan', password_hash=hasher.hash('untouched-isolated-password'), scope_mode='global')
        db.add(arpan)
        await db.flush()
        role = await db.scalar(select(UserRole.role_id).where(UserRole.user_id == UUID(administrator['id'])))
        db.add(UserRole(user_id=arpan.id, role_id=role))
        for n in range(2):
            db.add(Facility(name=f'Imported {n}', code=f'FD1-{n}'))
        db.add(Medicine(name='Imported medicine', code='MD1-0', unit='unspecified'))
        await db.flush()
        seed = await seed_operations(db, await db.get(User, UUID(administrator['id'])), 123, 2, 1)
        before = await identity_snapshot(db, 'arpan')
        result = await provision_matrix(db, sources, 123)
        assert result['created'] == 3
        count = await db.scalar(select(func.count()).select_from(User))
        again = await provision_matrix(db, sources, 123)
        assert again['created'] == 0
        assert await db.scalar(select(func.count()).select_from(User)) == count
        assert await identity_snapshot(db, 'arpan') == before
        assert secret not in json.dumps(again)
        assert {row['role'] for row in result['accounts']} == {role for role, _ in PROFILES.values()}
        assert 'admin' in again['roles_without_seed_profile']  # Test fixture role is reported, not fabricated.
    for profile, (role, permissions) in PROFILES.items():
        response = await client.post('/api/v1/auth/login', data={'username': 'dev-data-' + profile, 'password': secret})
        assert response.status_code == 200
        client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
        me = (await client.get('/api/v1/users/me')).json()['data']
        assert me['roles'] == [role] and set(me['permissions']) == permissions
        assert me['scope_mode'] == ('global' if profile == 'admin' else 'restricted')
        assert me['district_ids'] == []
        expected = [] if profile == 'admin' else seed['facility_ids'] + [seed['depot_id']] if profile == 'inventory' else seed['facility_ids'][:1]
        assert sorted(me['facility_ids']) == sorted(expected)
        assert (await client.get('/api/v1/inventory', params={'facility_id': seed['facility_ids'][0]})).status_code == 200
        assert (await client.get('/api/v1/users')).status_code == (200 if profile == 'admin' else 403)
        assert (await client.post('/api/v1/auth/logout')).status_code == 200
        assert (await client.get('/api/v1/users/me')).status_code == 401
    async with factory.begin() as db:
        wrong = {**sources, 'reader': ('different-isolated-password', 'environment')}
        with pytest.raises(ValueError, match='never resets'):
            await provision_matrix(db, wrong, 123)
        assert await identity_snapshot(db, 'arpan') == before


@pytest.mark.asyncio
async def test_account_matrix_requires_owned_seed(api):
    _, factory, _ = api
    async with factory.begin() as db:
        await create_user(db, 'admin', 'isolated-matrix-password', [])
        with pytest.raises(ValueError, match='existing owned'):
            await provision_matrix(db, {}, 999)
