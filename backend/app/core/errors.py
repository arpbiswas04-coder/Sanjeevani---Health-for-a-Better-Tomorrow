from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException


def install_error_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        codes = {401: 'UNAUTHENTICATED', 403: 'FORBIDDEN', 404: 'NOT_FOUND',
                 409: 'CONFLICT', 422: 'INVALID_INPUT', 503: 'SERVICE_UNAVAILABLE'}
        return JSONResponse(status_code=exc.status_code, headers=exc.headers,
            content={'success': False, 'error': {'code': codes.get(exc.status_code, 'HTTP_ERROR'), 'message': str(exc.detail)}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={'success': False,
            'error': {'code': 'VALIDATION_ERROR', 'message': 'Request fields are missing or invalid'}})

    @app.exception_handler(IntegrityError)
    async def conflict(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={'success': False,
            'error': {'code': 'CONFLICT', 'message': 'Record conflicts with existing data or database constraints'}})
