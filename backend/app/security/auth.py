from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models import User, UserRole, RolePermission, Permission

hasher = PasswordHasher()
oauth2 = OAuth2PasswordBearer(tokenUrl=f'{settings.API_V1_STR}/auth/login')


def verify_password(password, password_hash):
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def secret():
    if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 32:
        raise HTTPException(503, 'Authentication is not configured')
    return settings.JWT_SECRET


def access_token(user_id, version=0, session_id=None):
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user_id), 'iat': now, 'exp': now + timedelta(minutes=15),
                       'type': 'access', 'iss': 'sanjeevani', 'ver': version, 'sid': str(session_id) if session_id else None}, secret(), algorithm='HS256')


async def current_user(token: str = Depends(oauth2), db: AsyncSession = Depends(get_db, scope="function")):
    key = secret()
    try:
        payload = jwt.decode(token, key, algorithms=['HS256'], issuer='sanjeevani',
                             options={'require': ['sub', 'exp', 'iat', 'type']})
        if payload['type'] != 'access':
            raise ValueError()
        user_id = UUID(payload['sub'])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(401, 'Invalid or expired access token', headers={'WWW-Authenticate': 'Bearer'})
    user = await db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(401, 'Inactive or unknown user')
    if payload.get('ver', 0) != user.token_version:
        raise HTTPException(401, 'Session revoked')
    if payload.get('sid'):
        from app.models.identity import AuthSession
        try:
            sid = UUID(payload['sid'])
        except (ValueError, TypeError):
            raise HTTPException(401, 'Invalid session')
        session = await db.get(AuthSession, sid)
        from app.services.identity import aware
        if not session or session.user_id != user.id or session.revoked or aware(session.expires_at) <= datetime.now(timezone.utc):
            raise HTTPException(401, 'Session revoked')
    return user


def require(permission):
    async def check(user: User = Depends(current_user), db: AsyncSession = Depends(get_db, scope="function")):
        query = (select(Permission.id).join(RolePermission, RolePermission.permission_id == Permission.id)
                 .join(UserRole, UserRole.role_id == RolePermission.role_id)
                 .where(UserRole.user_id == user.id, Permission.name == permission))
        if not await db.scalar(query):
            raise HTTPException(403, 'Permission denied')
        return user
    return check
