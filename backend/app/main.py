import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.db.session import engine

# Configurar logging seguro
logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestión del ciclo de vida de la aplicación FastAPI."""
    logger.info("Iniciando %s en entorno [%s]", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Cerrando conexiones del motor de base de datos...")
    await engine.dispose()
    logger.info("Aplicación detenida correctamente.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API REST para LINGUA — Plataforma Computacional para la Investigación "
        "y Caracterización del Lenguaje en Personas con Afasia. "
        "Proporciona gestión clínica, consentimientos, administración de evaluaciones y catálogos."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configuración de CORS restringido a los orígenes definidos
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --- Manejadores Centralizados de Excepciones ---

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Manejo centralizado de excepciones de dominio de LINGUA."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Manejo centralizado de fallos de validación en esquemas de entrada (Pydantic)."""
    # Formatear errores legibles sin filtrar datos sensibles
    errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field_path,
            "message": err.get("msg", "Error de validación"),
            "type": err.get("type", "value_error"),
        })

    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Los datos proporcionados en la petición no cumplen con el formato o las reglas requeridas.",
                "details": errors,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Manejo de excepciones no controladas para evitar fugas de información interna."""
    logger.exception("Error inesperado en servidor: %s", type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Ha ocurrido un error interno en el servidor. Por favor, intente más tarde.",
                "details": None,
            }
        },
    )


# Registrar routers bajo /api/v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Ruta raíz que proporciona información básica de la API y enlace a la documentación."""
    return {
        "name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health",
    }
