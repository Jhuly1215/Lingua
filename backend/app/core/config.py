import re
from typing import Any, List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación LINGUA.
    Carga variables desde el entorno o archivo .env con validación estricta.
    """

    # --- Aplicación ---
    APP_NAME: str = "LINGUA Backend API"
    APP_ENV: str = "development"  # development | testing | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return []

    # --- Base de Datos (PostgreSQL en Supabase) ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/lingua_db",
        description="URL de conexión a PostgreSQL. Para asyncpg usar postgresql+asyncpg://",
    )

    # Parámetros para Supabase Pooler (PgBouncer modo transaccional, puerto 6543)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 300
    DB_POOL_PRE_PING: bool = True

    # --- Supabase Auth y Storage ---
    SUPABASE_URL: str = "https://placeholder-project.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # --- JWT / Seguridad ---
    JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"

    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV.lower() == "testing"

    @property
    def is_pooler(self) -> bool:
        """Determina si la conexión apunta al pooler de Supabase (puerto 6543 o PgBouncer)."""
        return ":6543" in self.DATABASE_URL or "pooler.supabase.com" in self.DATABASE_URL

    @property
    def async_database_url(self) -> str:
        """
        Garantiza que la URL tenga el esquema de driver asíncrono para SQLAlchemy:
        - Si es postgresql:// convierte a postgresql+asyncpg://
        - Si es sqlite:// convierte a sqlite+aiosqlite://
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """
        URL sincrónica para migraciones con Alembic (psycopg o sqlite).
        """
        url = self.DATABASE_URL
        if "postgresql+asyncpg://" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        elif "sqlite+aiosqlite://" in url:
            url = url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url

    def safe_repr(self) -> dict:
        """Retorna una versión sanitizada de la configuración para propósitos de depuración/diagnóstico."""
        data = self.model_dump()
        for secret_key in [
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_JWT_SECRET",
            "DATABASE_URL",
        ]:
            if data.get(secret_key):
                val = str(data[secret_key])
                if len(val) > 8:
                    data[secret_key] = f"{val[:4]}...{val[-4:]}"
                else:
                    data[secret_key] = "***"
        return data


settings = Settings()
