from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine


@asynccontextmanager
async def lifespan(app):
    if settings.APP_ENV == "production":
        required = {'DATABASE_URL', 'REDIS_URL', 'FRONTEND_URL', 'BACKEND_URL', 'BACKEND_CORS_ORIGINS'}
        missing = required - settings.model_fields_set
        if missing:
            raise RuntimeError('Production requires explicit configuration: ' + ', '.join(sorted(missing)))
        if not settings.DATABASE_URL or not settings.DATABASE_URL.startswith("postgresql"):
            raise RuntimeError("Production requires an explicit PostgreSQL DATABASE_URL")
        if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 32 or not settings.REDIS_URL:
            raise RuntimeError("Production authentication configuration is incomplete")
        if "*" in settings.BACKEND_CORS_ORIGINS:
            raise RuntimeError("Production CORS requires explicit origins")
    yield
    await engine.dispose()

from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import install_error_handlers
from app.api.v1.router import api_router

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description="Sanjeevani Grid - Health Resource Intelligence Platform Backend API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

install_error_handlers(app)
from app.core.context import install_context
install_context(app)
from app.security.rate_limit import install_rate_limit
install_rate_limit(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


from app.schemas.outputs import RootInfo

@app.get("/", response_model=RootInfo)
def root():
    return {
        "service": "Sanjeevani Grid API",
        "documentation": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
