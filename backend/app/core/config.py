from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: str = "development"
    PROJECT_NAME: str = "Sanjeevani Grid"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Database
    POSTGRES_DB: str = "sanjeevani"
    POSTGRES_USER: str = "sanjeevani"
    POSTGRES_PASSWORD: str = "sanjeevani_dev"
    DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Security
    JWT_SECRET: Optional[str] = None
    JWT_REFRESH_SECRET: Optional[str] = None

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # External
    WEATHER_API_KEY: Optional[str] = None
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
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5432/{self.POSTGRES_DB}"


settings = Settings()
