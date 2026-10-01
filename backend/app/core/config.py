from typing import List, Optional
from pydantic import Field
from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
    )

    APP_ENV: str = "development"
    PROJECT_NAME: str = "Sanjeevani Grid"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Database
    POSTGRES_DB: str = "sanjeevani"
    POSTGRES_USER: str = "sanjeevani"
    POSTGRES_PASSWORD: str = ""
    DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Security
    JWT_SECRET: Optional[str] = None
    JWT_REFRESH_SECRET: Optional[str] = None
    AUTH_RATE_LIMIT: int = Field(20, ge=1, le=10000)
    AUTH_RATE_WINDOW_SECONDS: int = Field(60, ge=1, le=3600)

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # External
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_PROVIDER: Optional[str] = None
    WEATHER_CACHE_SECONDS: int = Field(600, ge=1, le=86400)
    BACKUP_RETENTION_DAYS: int = Field(30, ge=1, le=3650)
    BACKUP_MAX_AGE_HOURS: int = Field(24, ge=1, le=8760)
    BACKUP_STORAGE_NAME: Optional[str] = None
    MLFLOW_TRACKING_URI: Optional[str] = None
    FEDERATION_SERVER_HOST: Optional[str] = None
    FEDERATION_SERVER_PORT: Optional[int] = None

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return URL.create("postgresql+asyncpg", username=self.POSTGRES_USER, password=self.POSTGRES_PASSWORD, host="localhost", port=5432, database=self.POSTGRES_DB).render_as_string(hide_password=False)


settings = Settings()
