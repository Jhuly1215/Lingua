import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.clinical_event import ClinicalEventResponse
from app.schemas.protocol import AphasiaTypeResponse, SeverityLevelResponse, SubtestResponse


class EvaluationSubtestCreate(BaseModel):
    """Esquema de entrada para asociar una subprueba a una evaluación."""
    subtest_id: uuid.UUID = Field(..., description="ID de la subprueba del protocolo")
    duration_seconds: Optional[Decimal] = Field(None, gt=0, description="Duración efectiva en segundos (ej. 60 o 90s para FAS)")
    score: Optional[Decimal] = Field(None, description="Puntaje obtenido")
    status: Optional[str] = Field("PENDING", max_length=50)
    observations: Optional[str] = Field(None, description="Observaciones durante la aplicación de la subprueba")


class EvaluationSubtestResponse(BaseModel):
    """Respuesta de la asociación entre evaluación y subprueba."""
    evaluation_subtest_id: uuid.UUID
    evaluation_id: uuid.UUID
    subtest_id: uuid.UUID
    duration_seconds: Optional[Decimal] = None
    score: Optional[Decimal] = None
    status: Optional[str] = None
    observations: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    subtest: Optional[SubtestResponse] = None

    model_config = ConfigDict(from_attributes=True)


class EvaluationBase(BaseModel):
    """Atributos base de una sesión de evaluación."""
    protocol_id: uuid.UUID = Field(..., description="ID del protocolo utilizado")
    clinical_event_id: Optional[uuid.UUID] = Field(None, description="Evento neurológico asociado")
    aphasia_type_id: Optional[uuid.UUID] = Field(None, description="Tipo de afasia clínicamente establecido")
    severity_level_id: Optional[uuid.UUID] = Field(None, description="Nivel de severidad clínica observado")
    evaluation_date: datetime = Field(..., description="Fecha y hora de la evaluación")
    status: str = Field(default="PENDING", max_length=50)
    general_observations: Optional[str] = Field(None, description="Observaciones generales del profesional")


class EvaluationCreate(EvaluationBase):
    """Esquema para crear una evaluación para un paciente."""
    pass


class EvaluationUpdate(BaseModel):
    """Esquema para actualización parcial (PATCH) de una evaluación."""
    status: Optional[str] = Field(None, max_length=50)
    clinical_event_id: Optional[uuid.UUID] = None
    aphasia_type_id: Optional[uuid.UUID] = None
    severity_level_id: Optional[uuid.UUID] = None
    general_observations: Optional[str] = None
    active: Optional[bool] = None


class EvaluationResponse(EvaluationBase):
    """Respuesta completa de la evaluación con metadatos de auditoría."""
    evaluation_id: uuid.UUID
    patient_id: uuid.UUID
    evaluator_id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationDetailResponse(EvaluationResponse):
    """Respuesta detallada que incluye las subpruebas asociadas y entidades clínicas contextuales."""
    evaluation_subtests: List[EvaluationSubtestResponse] = []
    aphasia_type: Optional[AphasiaTypeResponse] = None
    severity_level: Optional[SeverityLevelResponse] = None
    clinical_event: Optional[ClinicalEventResponse] = None

    model_config = ConfigDict(from_attributes=True)
