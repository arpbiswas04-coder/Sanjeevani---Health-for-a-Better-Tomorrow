from app.schemas import outputs as out
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User, Role, Permission
from app.schemas.identity import RefreshInput, PasswordChange, ResetRequest, ResetConfirm, UserCreate, UserUpdate, RoleCreate
from app.security.auth import current_user, require
from app.security.scope import global_only
from app.services import identity, admin
from app.repositories.common import get_record, serialize

router = APIRouter(responses=out.ERROR_RESPONSES, tags=['Identity administration'])


def data(value=None):
    return {'success': True, 'data': value}


async def administrator(user: User = Depends(require('admin.users'))):
    global_only(user)
    return user


@router.get('/users/me', response_model=out.Success[out.CurrentUserView], response_model_exclude_unset=True)
async def me(user: User = Depends(current_user), db: AsyncSession = Depends(get_db, scope="function")):
    return data(await identity.profile(db, user))


@router.post('/auth/refresh', response_model=out.Success[out.TokenPair], response_model_exclude_unset=True)
async def refresh(payload: RefreshInput, db: AsyncSession = Depends(get_db, scope="function")):
    return data(await identity.rotate(db, payload.refresh_token))


@router.post('/auth/logout', response_model=out.Success[None], response_model_exclude_unset=True)
async def logout(user: User = Depends(current_user), db: AsyncSession = Depends(get_db, scope="function")):
    await identity.logout(db, user)
    return data()


@router.post('/auth/password/change', response_model=out.Success[None], response_model_exclude_unset=True)
async def password_change(payload: PasswordChange, user: User = Depends(current_user), db: AsyncSession = Depends(get_db, scope="function")):
    await identity.change_password(db, user, payload)
    return data()


@router.post('/auth/password/reset/request', status_code=202, response_model=out.Success[out.Message], response_model_exclude_unset=True)
async def reset_request(payload: ResetRequest, db: AsyncSession = Depends(get_db, scope="function")):
    await identity.request_reset(db, payload.username)
    return data({'message': 'If the account is eligible, recovery instructions will be delivered'})


@router.post('/auth/password/reset/confirm', response_model=out.Success[None], response_model_exclude_unset=True)
async def reset_confirm(payload: ResetConfirm, db: AsyncSession = Depends(get_db, scope="function")):
    await identity.confirm_reset(db, payload)
    return data()


@router.post('/users', status_code=201, response_model=out.Success[out.UserView], response_model_exclude_unset=True)
async def create_user(payload: UserCreate, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data(await admin.create_user(db, user, payload))


@router.get('/users', response_model=out.Success[list[out.UserView]], response_model_exclude_unset=True)
async def users(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data([serialize(row, ('token_version',)) for row in await db.scalars(select(User).order_by(User.id).offset(offset).limit(limit))])


@router.get('/users/{identifier}', response_model=out.Success[out.UserView], response_model_exclude_unset=True)
async def user_detail(identifier: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data(serialize(await get_record(db, User, identifier), ('token_version',)))


@router.patch('/users/{identifier}', response_model=out.Success[out.UserView], response_model_exclude_unset=True)
async def user_update(identifier: UUID, payload: UserUpdate, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data(await admin.update_user(db, user, identifier, payload))


@router.put('/users/{identifier}/roles/{role_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def assign_role(identifier: UUID, role_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    await admin.assign(db, user, identifier, role_id, 'role')
    return data()


@router.delete('/users/{identifier}/roles/{role_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def remove_role(identifier: UUID, role_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    await admin.assign(db, user, identifier, role_id, 'role', True)
    return data()


@router.put('/users/{identifier}/facilities/{facility_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def assign_facility(identifier: UUID, facility_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    await admin.assign(db, user, identifier, facility_id, 'facility')
    return data()


@router.delete('/users/{identifier}/facilities/{facility_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def remove_facility(identifier: UUID, facility_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    await admin.assign(db, user, identifier, facility_id, 'facility', True)
    return data()


@router.get('/roles', response_model=out.Success[list[out.RoleView]], response_model_exclude_unset=True)
async def roles(user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data([serialize(row) for row in await db.scalars(select(Role).order_by(Role.name).limit(200))])


@router.post('/roles', status_code=201, response_model=out.Success[out.RoleView], response_model_exclude_unset=True)
async def create_role(payload: RoleCreate, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data(await admin.create_role(db, user, payload))


@router.get('/permissions', response_model=out.Success[list[out.PermissionView]], response_model_exclude_unset=True)
async def permissions(user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    return data([serialize(row) for row in await db.scalars(select(Permission).order_by(Permission.name).limit(200))])

@router.get('/audit-logs', response_model=out.Success[list[out.AuditLogView]], response_model_exclude_unset=True)
async def audit_logs(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                     user: User = Depends(require('audit.read')), db: AsyncSession = Depends(get_db, scope="function")):
    from app.models import AuditLog
    global_only(user)
    rows = await db.scalars(select(AuditLog).order_by(AuditLog.created_at, AuditLog.id).offset(offset).limit(limit))
    return data([serialize(row) for row in rows])

@router.put('/roles/{identifier}/permissions/{permission_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def grant_permission(identifier: UUID, permission_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    from app.models import RolePermission
    from app.services.inventory import audit
    await get_record(db, Role, identifier, lock=True)
    await get_record(db, Permission, permission_id)
    if not await db.get(RolePermission, (identifier, permission_id)):
        db.add(RolePermission(role_id=identifier, permission_id=permission_id))
    audit(db, user.id, 'admin.permission_granted', {'role_id': str(identifier), 'permission_id': str(permission_id)})
    return data()


@router.delete('/roles/{identifier}/permissions/{permission_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def remove_permission(identifier: UUID, permission_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    from fastapi import HTTPException
    from app.models import RolePermission, UserRole
    from app.services.inventory import audit
    await get_record(db, Role, identifier, lock=True)
    if await db.get(UserRole, (user.id, identifier)):
        raise HTTPException(409, 'Cannot remove permissions from your own role')
    row = await db.get(RolePermission, (identifier, permission_id))
    if row:
        await db.delete(row)
    audit(db, user.id, 'admin.permission_removed', {'role_id': str(identifier), 'permission_id': str(permission_id)})
    return data()


@router.get('/admin/config', response_model=out.Success[out.PublicConfig], response_model_exclude_unset=True)
async def public_config(user: User = Depends(require('admin.config'))):
    from app.core.config import settings
    global_only(user)
    return data({'auth_rate_limit': settings.AUTH_RATE_LIMIT, 'auth_rate_window_seconds': settings.AUTH_RATE_WINDOW_SECONDS,
                 'weather_cache_seconds': settings.WEATHER_CACHE_SECONDS, 'backup_retention_days': settings.BACKUP_RETENTION_DAYS,
                 'backup_max_age_hours': settings.BACKUP_MAX_AGE_HOURS})

@router.put('/users/{identifier}/districts/{district_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def assign_district(identifier: UUID, district_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    await admin.assign(db, user, identifier, district_id, 'district')
    return data()


@router.delete('/users/{identifier}/districts/{district_id}', response_model=out.Success[None], response_model_exclude_unset=True)
async def remove_district(identifier: UUID, district_id: UUID, user: User = Depends(administrator), db: AsyncSession = Depends(get_db, scope="function")):
    await admin.assign(db, user, identifier, district_id, 'district', True)
    return data()
