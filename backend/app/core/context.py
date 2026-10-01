from contextvars import ContextVar
from uuid import UUID,uuid4

request_id=ContextVar('request_id',default=None)


def install_context(app):
    @app.middleware('http')
    async def context(request,call_next):
        try:
            identifier=str(UUID(request.headers.get('X-Request-ID','')))
        except (ValueError,TypeError):
            identifier=str(uuid4())
        token=request_id.set(identifier)
        try:
            response=await call_next(request)
            response.headers['X-Request-ID']=identifier
            response.headers['X-Content-Type-Options']='nosniff'
            response.headers['X-Frame-Options']='DENY'
            response.headers['Referrer-Policy']='no-referrer'
            if request.url.path.startswith('/api/v1/auth') or request.url.path.startswith('/api/v1/users'):
                response.headers['Cache-Control']='no-store'
            return response
        finally:
            request_id.reset(token)
