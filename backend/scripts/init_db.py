"""
Script para inicializar tablas y esquemas en PostgreSQL / base de datos local.
Crea todas las tablas definidas en los modelos SQLAlchemy e inserta los catálogos base.
"""
import asyncio
import logging
import os
import sys

# Asegurar que el directorio raíz de backend esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from scripts.seed_catalogs import seed_all

logger = setup_logging("INFO")


async def init_db() -> None:
    logger.info("Inicializando esquema relacional de LINGUA...")
    async with engine.begin() as conn:
        # En PostgreSQL se puede habilitar pgcrypto / uuid-ossp si es necesario
        if "postgresql" in engine.url.drivername:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tablas creadas satisfactoriamente.")

    logger.info("Insertando catálogos iniciales...")
    async with AsyncSessionLocal() as session:
        await seed_all(session)
    logger.info("Base de datos inicializada y lista para su uso.")


if __name__ == "__main__":
    asyncio.run(init_db())
