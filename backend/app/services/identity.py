from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4
import asyncio
import jwt
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException
from sqlalchemy import select, update
from app.models import User
from app.models.identity import AuthSession, PasswordReset
from app.security.auth import hasher, verify_password, secret, access_token
from app.services.inventory import audit
from app.integrations import identity as adapters

DUMMY_HASH = hasher.hash('unused-login-timing-password')


def digest(token):
    return sha256(token.encode()).hexdigest()


def now():
    return datetime.now(timezone.utc)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def refresh_token(session, user):
    return jwt.encode({'sub': str(user.id), 'sid': str(session.id), 'jti': str(uuid4()),
                       'iat': now(), 'exp': session.expires_at, 'iss': 'sanjeevani', 'type': 'refresh'},
                      secret(), algorithm='HS256')


async def pair(db, user, session=None):
    if session is None:
        session = AuthSession(id=uuid4(), user_id=user.id, token_hash=digest(token_urlsafe(48)),
                              expires_at=now() + timedelta(days=7), revoked=False)
        db.add(session)
    token = refresh_token(session, user)
    session.token_hash = digest(token)
    await db.flush()
    return {'access_token': access_token(user.id, user.token_version, session.id),
            'refresh_token': token, 'token_type': 'bearer', 'expires_in': 900}


async def login(db, username, password, mfa_proof=None):
    if len(username)>120 or len(password)>1024:
        raise HTTPException(401, 'Invalid credentials')
    user = await db.scalar(select(User).where(User.username == username).with_for_update().execution_options(populate_existing=True))
    valid = await run_in_threadpool(verify_password, password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.active:
        raise HTTPException(401, 'Invalid credentials')
    if user.mfa_required:
        if not adapters.mfa_verifier or not mfa_proof:
            raise HTTPException(401, 'Additional authentication required')
        try:
            verified = await asyncio.wait_for(adapters.mfa_verifier.verify(user.id, mfa_proof), timeout=5)
        except Exception:
            raise HTTPException(503, 'Additional authentication temporarily unavailable')
        if not verified:
            raise HTTPException(401, 'Additional authentication required')
    result = await pair(db, user)
    audit(db, user.id, 'auth.login', {})
    return result


async def rotate(db, token):
    try:
        claims = jwt.decode(token, secret(), algorithms=['HS256'], issuer='sanjeevani',
                            options={'require': ['sub', 'sid', 'jti', 'iat', 'exp', 'type']})
        if claims['type'] != 'refresh':
            raise ValueError()
        uid, sid = UUID(claims['sub']), UUID(claims['sid'])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(401, 'Invalid refresh token')
    user = await db.scalar(select(User).where(User.id == uid).with_for_update().execution_options(populate_existing=True))
    session = await db.scalar(select(AuthSession).where(AuthSession.id == sid).with_for_update().execution_options(populate_existing=True))
    if not user or not user.active or not session or session.user_id != uid or session.revoked or aware(session.expires_at) <= now():
        raise HTTPException(401, 'Invalid refresh token')
    if session.token_hash != digest(token):
        # Persist family revocation even though this request is rejected.
        session.revoked = True
        audit(db, uid, 'auth.refresh_replay', {'session_id': str(sid)})
        await db.commit()
        raise HTTPException(401, 'Refresh token has already been used')
    audit(db, uid, 'auth.refresh', {'session_id': str(sid)})
    return await pair(db, user, session)


async def revoke_all(db, user):
    user.token_version += 1
    await db.execute(update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True))


async def logout(db, actor):
    user = await db.scalar(select(User).where(User.id == actor.id).with_for_update().execution_options(populate_existing=True))
    await revoke_all(db, user)
    audit(db, user.id, 'auth.logout', {})


async def change_password(db, actor, payload):
    user = await db.scalar(select(User).where(User.id == actor.id).with_for_update().execution_options(populate_existing=True))
    if not await run_in_threadpool(verify_password, payload.current_password.get_secret_value(), user.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    user.password_hash = await run_in_threadpool(hasher.hash, payload.new_password.get_secret_value())
    await revoke_all(db, user)
    await db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id).values(used=True))
    audit(db, user.id, 'auth.password_changed', {})


async def request_reset(db, username):
    user = await db.scalar(select(User).where(User.username == username).with_for_update().execution_options(populate_existing=True))
    if not user or not user.active or adapters.reset_delivery is None:
        return
    token = token_urlsafe(48)
    await db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id).values(used=True))
    reset = PasswordReset(user_id=user.id, token_hash=digest(token), expires_at=now() + timedelta(minutes=15))
    db.add(reset)
    await db.flush()
    # Adapter is responsible for trusted account recovery address lookup.
    try:
        await asyncio.wait_for(adapters.reset_delivery.deliver(user.id, token), timeout=5)
    except Exception:
        reset.used = True
        audit(db, user.id, 'auth.reset_delivery_failed', {})
        return
    audit(db, user.id, 'auth.reset_requested', {})


async def confirm_reset(db, payload):
    reset = await db.scalar(select(PasswordReset).where(PasswordReset.token_hash == digest(payload.token)))
    if not reset:
        raise HTTPException(400, 'Invalid or expired reset token')
    user = await db.scalar(select(User).where(User.id == reset.user_id).with_for_update().execution_options(populate_existing=True))
    reset = await db.scalar(select(PasswordReset).where(PasswordReset.id == reset.id).with_for_update().execution_options(populate_existing=True))
    if reset.used or aware(reset.expires_at) <= now() or not user.active:
        raise HTTPException(400, 'Invalid or expired reset token')
    reset.used = True
    user.password_hash = await run_in_threadpool(hasher.hash, payload.new_password.get_secret_value())
    await revoke_all(db, user)
    await db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id).values(used=True))
    audit(db, user.id, 'auth.password_reset', {})
