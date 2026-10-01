"""Explicit local administrator bootstrap; never runs during API startup."""
import asyncio
from getpass import getpass
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine
from app.models import User, Role, Permission, UserRole, RolePermission
from app.security.auth import hasher

from app.security.permissions import PERMISSIONS


async def create_admin(username, password):
    if not username.strip() or len(username) > 120 or len(password) < 12:
        raise ValueError('Use a username of 1-120 characters and a password of at least 12 characters')
    async with AsyncSessionLocal.begin() as db:
        if await db.scalar(select(User.id).where(User.username == username)):
            raise ValueError('Username already exists')
        role = await db.scalar(select(Role).where(Role.name == 'administrator'))
        if not role:
            role = Role(name='administrator')
            db.add(role)
            await db.flush()
        for name in PERMISSIONS:
            permission = await db.scalar(select(Permission).where(Permission.name == name))
            if not permission:
                permission = Permission(name=name)
                db.add(permission)
                await db.flush()
            if not await db.get(RolePermission, (role.id, permission.id)):
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))
        user = User(username=username, scope_mode='global', password_hash=hasher.hash(password))
        db.add(user)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
    await engine.dispose()


if __name__ == '__main__':
    username = input('Administrator username: ').strip()
    password = getpass('Password (at least 12 characters): ')
    if password != getpass('Confirm password: '):
        raise SystemExit('Passwords do not match')
    asyncio.run(create_admin(username, password))
    print('Administrator created')
