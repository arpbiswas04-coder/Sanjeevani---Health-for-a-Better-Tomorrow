import hashlib
import threading
import time
from collections import deque
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from app.core.config import settings

_local={}
_lock=threading.Lock()
_SCRIPT="local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n"


async def allowed(key):
    if settings.APP_ENV=='testing':
        return True
    if settings.APP_ENV=='production':
        if not settings.REDIS_URL:
            raise RuntimeError('Rate limit storage unavailable')
        async with Redis.from_url(settings.REDIS_URL,socket_connect_timeout=2,socket_timeout=2) as redis:
            count=await redis.eval(_SCRIPT,1,'auth-limit:'+key,settings.AUTH_RATE_WINDOW_SECONDS)
        return count<=settings.AUTH_RATE_LIMIT
    now=time.monotonic()
    with _lock:
        if len(_local)>=10000:
            for old in list(_local):
                if not _local[old] or _local[old][-1]<now-settings.AUTH_RATE_WINDOW_SECONDS:
                    del _local[old]
            if len(_local)>=10000 and key not in _local:
                return False
        events=_local.setdefault(key,deque())
        while events and events[0]<now-settings.AUTH_RATE_WINDOW_SECONDS:
            events.popleft()
        if len(events)>=settings.AUTH_RATE_LIMIT:
            return False
        events.append(now)
        return True


def install_rate_limit(app):
    @app.middleware('http')
    async def rate_limit(request,call_next):
        sensitive=('/auth/login','/auth/refresh','/auth/password/reset/request','/auth/password/reset/confirm')
        if request.method=='POST' and request.url.path in {settings.API_V1_STR+p for p in sensitive}:
            # Do not trust caller-provided forwarding headers. Configure proxy trust at ASGI deployment.
            address=request.client.host if request.client else 'unknown'
            key=hashlib.sha256((request.url.path+':'+address).encode()).hexdigest()
            try:
                permit=await allowed(key)
            except Exception:
                return JSONResponse(status_code=503,content={'success':False,'error':{'code':'AUTH_UNAVAILABLE','message':'Authentication temporarily unavailable'}})
            if not permit:
                return JSONResponse(status_code=429,headers={'Retry-After':str(settings.AUTH_RATE_WINDOW_SECONDS)},
                    content={'success':False,'error':{'code':'RATE_LIMITED','message':'Too many authentication requests'}})
        return await call_next(request)
