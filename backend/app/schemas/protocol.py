import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AphasiaTypeResponse(BaseModel):
    """Información del catálogo clínico de afasias."""
    aphasia_type_id: uuid.UUID
    name: str
    description: Optional[str] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class SeverityLevelResponse(BaseModel):
    """Información del catálogo de niveles de severidad."""
    severity_level_id: uuid.UUID
    name: str
    description: Optional[str] = None
    min_score: Optional[Decimal] = None
    max_score: Optional[Decimal] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class SubtestResponse(BaseModel):
    """Información de una subprueba perteneciente a un protocolo."""
    subtest_id: uuid.UUID
    protocol_id: uuid.UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    order_number: Optional[int] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ProtocolResponse(BaseModel):
    """Información general de un protocolo de evaluación."""
    protocol_id: uuid.UUID
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ProtocolDetailResponse(ProtocolResponse):
    """Detalle completo del protocolo con su lista ordenada de subpruebas."""
    subtests: List[SubtestResponse] = []

    model_config = ConfigDict(from_attributes=True)
