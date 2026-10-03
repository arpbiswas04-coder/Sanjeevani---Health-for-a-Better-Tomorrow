"""Manual-account matrix for the existing guarded development seeder.

Never creates a permission profile from a frontend presentation alias. Never
resets passwords. Public results contain password sources, not password values.
"""
import json
import os
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, Role, Permission, RolePermission, UserRole, UserFacility, MutationReceipt
from app.models.identity import UserDistrict
from scripts.development_data import guard, actor
from scripts.development_seed import PROFILES, create_user

CATEGORIES = {'admin': 'System administrator', 'operator': 'Facility operations',
              'inventory': 'Warehouse / inventory', 'reader': 'Read-only facility'}


async def identity_snapshot(db, username):
    """Private comparison only; never emit password hashes or identity contents."""
    user = await db.scalar(select(User).where(User.username == username))
    if user is None:
        return None
    roles = list(await db.scalars(select(UserRole.role_id).where(UserRole.user_id == user.id)))
    def normalized(value):
        if isinstance(value, datetime):
            return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)).isoformat()
        return value
    return {
        'columns': {column.name: normalized(getattr(user, column.name)) for column in User.__table__.columns},
        'roles': sorted(map(str, roles)),
        'permissions': sorted(set(await db.scalars(select(Permission.name).join(RolePermission)
                                                 .where(RolePermission.role_id.in_(roles))))),
        'facilities': sorted(map(str, await db.scalars(select(UserFacility.facility_id).where(UserFacility.user_id == user.id)))),
        'districts': sorted(map(str, await db.scalars(select(UserDistrict.district_id).where(UserDistrict.user_id == user.id)))),
    }


def passwords(credentials_file=None):
    shared = os.environ.get('SANJEEVANI_DEV_TEST_PASSWORD')
    if shared:
        return {key: (shared, 'SANJEEVANI_DEV_TEST_PASSWORD') for key in PROFILES}
    if credentials_file is None:
        raise ValueError('Supply SANJEEVANI_DEV_TEST_PASSWORD or an explicit private --credentials-file; existing passwords are never reset')
    records = json.loads(credentials_file.read_text())
    result = {}
    for key in PROFILES:
        record = records[key]
        if record['username'] != 'dev-data-' + key:
            raise ValueError('Private credentials must match the owned development usernames')
        result[key] = (record['password'], f'Private credentials file: {key}.password')
    return result


async def provision_matrix(db, secret_sources, seed):
    owner = await actor(db)
    receipt = await db.scalar(select(MutationReceipt).where(MutationReceipt.actor_id == owner.id,
        MutationReceipt.operation == 'devdata.operations', MutationReceipt.key == str(seed)))
    if not receipt:
        raise ValueError('An existing owned development operations seed is required')
    facilities = [UUID(value) for value in receipt.response['facility_ids']]
    if not facilities:
        raise ValueError('Seed has no facility scope')
    scopes = {'admin': [], 'operator': facilities[:1], 'reader': facilities[:1],
              'inventory': facilities + [UUID(receipt.response['depot_id'])]}
    before = await identity_snapshot(db, 'arpan')
    result = []
    for profile in PROFILES:
        password, source = secret_sources[profile]
        entry = await create_user(db, profile, password, scopes[profile])
        # These profiles own explicit facility assignments, never implicit districts.
        if await db.scalar(select(UserDistrict.user_id).where(UserDistrict.user_id == UUID(entry['id']))):
            raise ValueError('Existing development account has unexpected district scope; no account changed')
        result.append({**entry, 'category': CATEGORIES[profile], 'password_source': source,
            'scope_mode': 'global' if profile == 'admin' else 'restricted',
            'permissions': sorted(PROFILES[profile][1]),
            'portal': 'SUPER_ADMIN' if profile == 'admin' else 'FACILITY_ADMIN',
            'landing_page': '/admin/dashboard' if profile == 'admin' else '/facility/dashboard'})
    await db.flush()
    if before != await identity_snapshot(db, 'arpan'):
        raise RuntimeError('Protected administrator changed; transaction aborted')
    catalogue = []
    for role in await db.scalars(select(Role).order_by(Role.name)):
        catalogue.append({'role': role.name, 'permissions': sorted(await db.scalars(
            select(Permission.name).join(RolePermission).where(RolePermission.role_id == role.id)))})
    covered = {entry['role'] for entry in result}
    return {'accounts': result, 'created': sum(entry['created'] for entry in result),
            'arpan_unchanged': True, 'roles': catalogue,
            'roles_without_seed_profile': [role['role'] for role in catalogue if role['role'] not in covered]}


async def accounts(args):
    secret_sources = passwords(args.credentials_file)
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        return await provision_matrix(db, secret_sources, args.seed)
