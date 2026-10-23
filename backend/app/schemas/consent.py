import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConsentBase(BaseModel):
    """Atributos de consentimiento informado (patient_consents)."""
    consent_type: str = Field(..., max_length=50, description="Finalidad del consentimiento (ej. EVALUATION, RESEARCH, AUDIO_RECORDING)")
    consent_status: Literal["GRANTED", "DENIED", "WITHDRAWN"] = Field(..., description="Estado del consentimiento")
    consent_date: datetime = Field(..., description="Fecha y hora en que se otorgó o modificó el consentimiento")
    version: str = Field(default="1.0", max_length=50, description="Versión del documento de consentimiento informado")
    notes: Optional[str] = Field(None, description="Observaciones o notas adicionales")


class ConsentCreate(ConsentBase):
    """Esquema de entrada para registrar consentimiento."""
    pass


class ConsentResponse(ConsentBase):
    """Esquema de salida con trazabilidad."""
    consent_id: uuid.UUID
    patient_id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
