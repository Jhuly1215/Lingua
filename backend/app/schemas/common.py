from typing import Generic, List, Optional, TypeVar, Any
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Esquema genérico para respuestas paginadas con metadatos."""
    items: List[T]
    total: int = Field(..., ge=0, description="Total de registros existentes")
    page: int = Field(..., ge=1, description="Página actual")
    size: int = Field(..., ge=1, description="Cantidad de registros por página")
    pages: int = Field(..., ge=0, description="Total de páginas disponibles")

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Estructura estandarizada de errores devueltos por la API de LINGUA."""
    code: str = Field(..., description="Código de error estandarizado en mayúsculas")
    message: str = Field(..., description="Mensaje amigable para el cliente")
    details: Optional[Any] = Field(None, description="Detalles adicionales del error")


class ErrorResponse(BaseModel):
    """Envoltorio principal de error."""
    error: ErrorDetail


class HealthResponse(BaseModel):
    """Estado general del servicio API."""
    status: str = Field(..., examples=["healthy"])
    app_name: str
    environment: str
    version: str = "0.1.0"


class DatabaseHealthResponse(BaseModel):
    """Estado de conectividad y latencia con Supabase PostgreSQL."""
    status: str
    database: str
    latency_ms: float
    pooler_mode: bool
