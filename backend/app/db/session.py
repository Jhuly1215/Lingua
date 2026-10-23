import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger("lingua.db")

# Construcción de argumentos de conexión según motor y proveedor
connect_args = {}

if "postgresql+asyncpg" in settings.async_database_url:
    # Para Supabase con PgBouncer en puerto 6543 (Transaction Pooler):
    # asyncpg debe tener statement_cache_size=0 para evitar fallos de PREPARE
    if settings.is_pooler:
        logger.info("Configurando conexión asyncpg para Supabase Transaction Pooler (PgBouncer: 6543).")
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0

    # Configuración SSL recomendada para PostgreSQL en la nube
    # En desarrollo local contra docker o localhost se puede omitir si no tiene SSL
    if "localhost" not in settings.async_database_url and "127.0.0.1" not in settings.async_database_url:
        connect_args["ssl"] = "require"

engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_recycle": settings.DB_POOL_RECYCLE,
    "pool_pre_ping": settings.DB_POOL_PRE_PING,
    "connect_args": connect_args,
}

if "sqlite" not in settings.async_database_url:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI que proporciona una sesión de base de datos asíncrona.
    Maneja el commit automático en éxito, rollback en excepción y cierre de la sesión.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> dict:
    """
    Comprueba activamente la conectividad con el motor de base de datos ejecutando 'SELECT 1'.
    Retorna un diccionario con estado, latencia o mensaje de error.
    """
    import time
    start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            if value == 1:
                return {
                    "status": "healthy",
                    "database": "connected",
                    "latency_ms": latency_ms,
                    "pooler_mode": settings.is_pooler,
                }
            return {
                "status": "unhealthy",
                "database": "unexpected_result",
                "latency_ms": latency_ms,
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("Error comprobando conectividad con la base de datos: %s", type(exc).__name__)
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error_type": type(exc).__name__,
            "latency_ms": latency_ms,
        }
