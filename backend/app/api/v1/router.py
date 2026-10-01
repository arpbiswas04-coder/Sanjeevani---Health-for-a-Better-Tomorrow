from fastapi import APIRouter
from app.api.v1.endpoints import health, platform

api_router = APIRouter()
api_router.include_router(health.router, tags=['Health'])
api_router.include_router(platform.router)

from app.api.v1.endpoints import identity
api_router.include_router(identity.router)

from app.api.v1.endpoints import geography
api_router.include_router(geography.router)

from app.api.v1.endpoints import stock
api_router.include_router(stock.router)

from app.api.v1.endpoints import transfers
api_router.include_router(transfers.router)

from app.api.v1.endpoints import supply
api_router.include_router(supply.router)

from app.api.v1.endpoints import operations
api_router.include_router(operations.router)

from app.api.v1.endpoints import alerts
api_router.include_router(alerts.router)

from app.api.v1.endpoints import assets
api_router.include_router(assets.router)

from app.api.v1.endpoints import reports
api_router.include_router(reports.router)

from app.api.v1.endpoints import sync
api_router.include_router(sync.router)

from app.api.v1.endpoints import integrations
api_router.include_router(integrations.router)

from app.api.v1.endpoints import report_jobs
api_router.include_router(report_jobs.router)
