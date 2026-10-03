"""Explicit development portal policies using existing capability/district grants.

State grants are a snapshot of the state's existing districts, not a new scope
mode. No source geography is created or edited. Not run by application startup.
"""
import json
import os
from pathlib import Path
from secrets import token_urlsafe
from uuid import UUID
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, Role, Permission, RolePermission, UserRole, UserFacility, Facility, State, District, Block, AuditLog
from app.models.identity import UserDistrict
from app.security.auth import hasher, verify_password
from app.services.inventory import audit
from scripts.development_data import guard, ROOT
from scripts.development_accounts import identity_snapshot
from scripts.development_seed import READ

OPERATIONS = set(READ) | {'inventory.write','beds.write','workforce.write','equipment.write','alerts.manage'}
POLICIES = {
    'national': OPERATIONS | {'inventory.transfer','procurement.write','procurement.approve'},
    'state': OPERATIONS | {'inventory.transfer','procurement.write'},
    'district': OPERATIONS,
    'facility': OPERATIONS,
}


async def jurisdiction(db, state_id, district_id, facility_id):
    state = await db.get(State, state_id)
    district = await db.get(District, district_id)
    facility = await db.get(Facility, facility_id)
    block = await db.get(Block, facility.block_id) if facility and facility.block_id else None
    if not state or not district or district.state_id != state.id or not facility or not facility.active or not block or block.district_id != district.id:
        raise ValueError('Existing active facility -> block -> district -> state hierarchy required; no geography invented')
    districts = set(await db.scalars(select(District.id).where(District.state_id == state.id)))
    return {'state': state, 'district': district, 'facility': facility, 'state_districts': districts}


async def provision(db, credentials, state_id, district_id, facility_id):
    geography = await jurisdiction(db, state_id, district_id, facility_id)
    before = await identity_snapshot(db, 'arpan')
    result = []
    for level, permissions in POLICIES.items():
        username = 'dev-' + level + '-admin'
        credential = credentials[level]
        if credential['username'] != username or not 12 <= len(credential['password']) <= 1024:
            raise ValueError('Invalid development credential record')
        role_name = level + '_admin'
        role = await db.scalar(select(Role).where(Role.name == role_name))
        if role:
            actual = set(await db.scalars(select(Permission.name).join(RolePermission).where(RolePermission.role_id == role.id)))
            if actual != permissions:
                raise ValueError('Existing role policy differs; refusing to change grants')
        else:
            catalogue = {p.name:p.id for p in await db.scalars(select(Permission))}
            if not permissions <= catalogue.keys():
                raise ValueError('Permission catalogue incomplete')
            role = Role(name=role_name); db.add(role); await db.flush()
            db.add_all([RolePermission(role_id=role.id, permission_id=catalogue[p]) for p in sorted(permissions)])
        districts = geography['state_districts'] if level == 'state' else {district_id} if level == 'district' else set()
        facilities = {facility_id} if level == 'facility' else set()
        mode = 'global' if level == 'national' else 'restricted'
        ownership = {'development_only':True, 'level':level, 'state_id':str(state_id),
                     'district_id':str(district_id), 'facility_id':str(facility_id)}
        user = await db.scalar(select(User).where(User.username == username))
        created = user is None
        if user:
            receipt = await db.scalar(select(AuditLog.details).where(AuditLog.actor_id == user.id, AuditLog.action == 'devportal.user.created'))
            roles = set(await db.scalars(select(UserRole.role_id).where(UserRole.user_id == user.id)))
            actual_districts = set(await db.scalars(select(UserDistrict.district_id).where(UserDistrict.user_id == user.id)))
            actual_facilities = set(await db.scalars(select(UserFacility.facility_id).where(UserFacility.user_id == user.id)))
            if receipt != ownership or roles != {role.id} or actual_districts != districts or actual_facilities != facilities or user.scope_mode != mode or not user.active:
                raise ValueError('Existing account/scope differs; refusing to overwrite')
            if not verify_password(credential['password'], user.password_hash):
                raise ValueError('Existing password differs; never reset by this command')
        else:
            user = User(username=username, password_hash=hasher.hash(credential['password']), scope_mode=mode)
            db.add(user); await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.add_all([UserDistrict(user_id=user.id, district_id=d) for d in districts])
            db.add_all([UserFacility(user_id=user.id, facility_id=f) for f in facilities])
            audit(db, user.id, 'devportal.user.created', ownership)
        result.append({'username':username, 'role':role_name, 'created':created, 'scope_mode':mode,
                       'district_ids':sorted(map(str,districts)), 'facility_ids':sorted(map(str,facilities)),
                       'permissions':sorted(permissions), 'landing_page':f'/{level}/dashboard'})
    await db.flush()
    if before != await identity_snapshot(db, 'arpan'):
        raise RuntimeError('Protected administrator changed; abort transaction')
    return {'accounts':result, 'arpan_unchanged':True,
            'state':{'id':str(state_id),'name':geography['state'].name},
            'district':{'id':str(district_id),'name':geography['district'].name},
            'facility':{'id':str(facility_id),'name':geography['facility'].name}}


def local_credentials(path):
    # Only the already ignored private workspace directory may contain this file.
    path = path.resolve()
    if not path.is_relative_to((ROOT/'tmp').resolve()):
        raise ValueError('Credential file must be in the ignored workspace tmp directory')
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    shared = os.environ.get('SANJEEVANI_DEV_TEST_PASSWORD')
    if shared and not 12 <= len(shared) <= 1024:
        raise ValueError('Shared test password must contain 12..1024 characters')
    records = {level:{'username':f'dev-{level}-admin','password':shared or token_urlsafe(24)} for level in POLICIES}
    path.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive create preserves any concurrently supplied private credentials.
    with path.open('x',encoding='utf-8') as file:
        json.dump(records,file,indent=2)
    return records


async def portals(args):
    async with AsyncSessionLocal.begin() as db:
        await guard(db)
        await jurisdiction(db,args.state_id,args.district_id,args.facility_id)
        credentials = local_credentials(args.credentials_file)
        return await provision(db,credentials,args.state_id,args.district_id,args.facility_id)
