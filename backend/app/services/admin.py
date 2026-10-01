from fastapi import HTTPException
from sqlalchemy import select
from app.models import User, Role, Permission, UserRole, RolePermission, Facility
from app.models.identity import UserFacility, UserDistrict
from app.models.geography import District
from app.repositories.common import get_record, serialize
from app.security.auth import hasher
from app.services.identity import revoke_all
from app.services.inventory import audit


async def create_user(db, actor, payload):
    user = User(username=payload.username, password_hash=hasher.hash(payload.password.get_secret_value()), scope_mode=payload.scope_mode)
    db.add(user)
    await db.flush()
    audit(db, actor.id, 'admin.user_created', {'user_id': str(user.id)})
    return serialize(user, ('token_version',))


async def update_user(db, actor, identifier, payload):
    user = await get_record(db, User, identifier, lock=True)
    changes = payload.model_dump(exclude_none=True)
    if user.id == actor.id and (changes.get('active') is False or changes.get('scope_mode') == 'restricted'):
        raise HTTPException(409, 'Cannot remove your own administrative access')
    for key, value in changes.items():
        setattr(user, key, value)
    await revoke_all(db, user)
    audit(db, actor.id, 'admin.user_updated', {'user_id': str(user.id), 'changes': changes})
    await db.flush()
    return serialize(user, ('token_version',))


async def assign(db, actor, user_id, resource_id, kind, remove=False):
    user = await get_record(db, User, user_id, lock=True)
    model, association, key = {'role': (Role, UserRole, 'role_id'), 'facility': (Facility, UserFacility, 'facility_id'), 'district': (District, UserDistrict, 'district_id')}[kind]
    await get_record(db, model, resource_id)
    if user_id == actor.id and remove and kind == 'role':
        raise HTTPException(409, 'Cannot remove your own role')
    row = await db.get(association, (user_id, resource_id))
    if remove and row:
        await db.delete(row)
    elif not remove and not row:
        db.add(association(user_id=user_id, **{key: resource_id}))
    await revoke_all(db, user)
    audit(db, actor.id, f'admin.{kind}_assignment', {'user_id': str(user_id), 'resource_id': str(resource_id), 'removed': remove})


async def create_role(db, actor, payload):
    role = Role(name=payload.name)
    db.add(role)
    await db.flush()
    for identifier in set(payload.permission_ids):
        await get_record(db, Permission, identifier)
        db.add(RolePermission(role_id=role.id, permission_id=identifier))
    audit(db, actor.id, 'admin.role_created', {'role_id': str(role.id)})
    return serialize(role)
