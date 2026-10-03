from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError, TimeoutError as PoolTimeout

Base = declarative_base()

engine = create_async_engine(settings.get_database_url(), pool_pre_ping=True, hide_parameters=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                yield session
    except (OperationalError, PoolTimeout, ConnectionError, OSError) as exc:
        raise HTTPException(503, 'Database unavailable; please try again later') from exc
