from fastapi import APIRouter, status
from app.core.config import settings
from app.db.session import check_database_connection
from app.schemas.common import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["Salud del Sistema"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Comprobación de salud de la API",
    description="Retorna el estado de disponibilidad general del servicio FastAPI sin consultar base de datos.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        version="0.1.0",
    )


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Comprobación de conectividad con Supabase PostgreSQL",
    description="Realiza una consulta ligera 'SELECT 1' contra PostgreSQL midiendo latencia y detectando modo pooler.",
)
async def get_database_health() -> DatabaseHealthResponse:
    result = await check_database_connection()
    return DatabaseHealthResponse(
        status=result["status"],
        database=result["database"],
        latency_ms=result.get("latency_ms", 0.0),
        pooler_mode=result.get("pooler_mode", False),
    )
