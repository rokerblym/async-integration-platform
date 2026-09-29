from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://appuser:apppassword@localhost:5433/integrationdb"
    sync_database_url: str = "postgresql+psycopg://appuser:apppassword@localhost:5433/integrationdb"
    redis_url: str = "redis://localhost:6380/0"
    downstream_url: str | None = None
    webhook_secret: str = "development-secret"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
