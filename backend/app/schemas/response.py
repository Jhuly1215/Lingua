import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FASErrorType(str, Enum):
    """
    Tipos de errores y eventos clínicos tipificados en el protocolo FAS
    (Controlled Oral Word Association — COWA).
    """
    PERSEVERATION = "PERSEVERATION"                        # Repetición de palabra ya dicha en el mismo ensayo
    PHONETIC_INTRUSION = "PHONETIC_INTRUSION"              # Palabra que no empieza con la letra fonológica requerida
    SEMANTIC_INTRUSION = "SEMANTIC_INTRUSION"              # Palabra que no pertenece a la categoría semántica
    PROPER_NOUN_NOT_ALLOWED = "PROPER_NOUN_NOT_ALLOWED"    # Nombre propio en condición prohibida (todas excepto Países)
    NEOLOGISM_PARAPHASIA = "NEOLOGISM_PARAPHASIA"          # Emisión no léxica o sustitución parafásica
    PROLONGED_PAUSE = "PROLONGED_PAUSE"                    # Bloqueo o silencio notable entre respuestas
    OTHER = "OTHER"                                        # Otro error clínico anotado por el examinador


class ResponseItemCreate(BaseModel):
    """Esquema para registrar una respuesta individual emitida por el paciente."""
    response_text: Optional[str] = Field(None, max_length=255, description="Palabra o emisión producida por el paciente")
    response_order: Optional[int] = Field(None, ge=1, description="Orden secuencial de la respuesta en la tarea")
    is_valid: bool = Field(True, description="Indica si la respuesta cumple la regla de la condición y es válida")
    error_type: Optional[FASErrorType] = Field(None, description="Tipo de error clínico si no es válida")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Tiempo de respuesta o latencia en milisegundos")
    start_time_ms: Optional[int] = Field(None, ge=0, description="Marca temporal de inicio de la emisión dentro de la tarea (ms)")
    end_time_ms: Optional[int] = Field(None, ge=0, description="Marca temporal de fin de la emisión dentro de la tarea (ms)")
    examiner_observation: Optional[str] = Field(None, description="Observación clínica del examinador")


class FASConditionResponsesCreate(BaseModel):
    """
    Esquema para el registro en lote de respuestas de una condición FAS
    (ej. Letra F, Letra A, Letra S o Semántica Animales).
    """
    responses: List[ResponseItemCreate] = Field(..., description="Lista ordenada de palabras/respuestas registradas")
    auto_detect_perseverations: bool = Field(
        True,
        description="Si es True, detecta automáticamente palabras duplicadas en el ensayo y las marca como PERSEVERATION",
    )
    duration_seconds: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Duración efectiva aplicada en la condición (ej. 60.000 segundos)",
    )


class ResponseResponse(BaseModel):
    """Esquema de salida de una respuesta registrada en base de datos."""
    response_id: uuid.UUID
    evaluation_id: uuid.UUID
    item_id: Optional[uuid.UUID]
    response_text: Optional[str]
    score: Optional[Decimal]
    is_valid: Optional[bool]
    error_type: Optional[str]
    response_order: Optional[int]
    response_time_ms: Optional[int]
    start_time_ms: Optional[int]
    end_time_ms: Optional[int]
    examiner_observation: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FASErrorsBreakdown(BaseModel):
    """
    Desglose clínico de errores e intrusiones.
    Criterio de aceptación US-09: No suman al puntaje, pero se conservan para investigación.
    """
    perseverations: int = Field(0, description="Total de repeticiones o perseveraciones")
    phonetic_intrusions: int = Field(0, description="Total de intrusiones fonéticas")
    semantic_intrusions: int = Field(0, description="Total de intrusiones semánticas")
    proper_nouns_not_allowed: int = Field(0, description="Total de nombres propios no permitidos")
    neologisms_paraphasias: int = Field(0, description="Total de neologismos y parafasias")
    prolonged_pauses: int = Field(0, description="Total de pausas prolongadas registradas")
    other_errors: int = Field(0, description="Total de otros errores clínicos")
    total_errors: int = Field(0, description="Suma total de errores e intrusiones conservadas")


class FASConditionScoreResponse(BaseModel):
    """
    Resultado y puntuación de una condición FAS específica (US-09).
    Cumple el criterio: conteo de respuestas válidas y conservación de repeticiones e intrusiones.
    """
    evaluation_id: uuid.UUID
    subtest_id: uuid.UUID
    subtest_name: str
    subtest_code: Optional[str]
    duration_seconds: Optional[Decimal]
    total_responses: int = Field(..., description="Total de emisiones registradas en la condición")
    valid_responses_count: int = Field(..., description="Puntaje oficial de la condición (solo respuestas válidas)")
    error_responses_count: int = Field(..., description="Total de emisiones descartadas por error o intrusión")
    errors_breakdown: FASErrorsBreakdown
    responses: List[ResponseResponse] = Field(default_factory=list, description="Listado de respuestas con su clasificación")


class FASEvaluationSummaryResponse(BaseModel):
    """
    Resumen consolidado de puntuación FAS para toda la evaluación.
    Agrupa las condiciones fonológicas (F, A, S) y semánticas con sus subtotales y total general.
    """
    evaluation_id: uuid.UUID
    patient_id: uuid.UUID
    patient_code: str
    phonetic_score: int = Field(..., description="Puntuación acumulada de fluencia fonética (F + A + S)")
    semantic_score: int = Field(..., description="Puntuación acumulada de fluencia semántica (Animales, etc.)")
    total_fas_score: int = Field(..., description="Puntuación total general FAS (suma de respuestas válidas)")
    total_responses: int = Field(..., description="Total global de emisiones de todas las condiciones")
    total_errors: int = Field(..., description="Total global de errores e intrusiones conservadas")
    errors_breakdown: FASErrorsBreakdown
    conditions: List[FASConditionScoreResponse] = Field(default_factory=list, description="Puntuaciones detalladas por cada condición")
