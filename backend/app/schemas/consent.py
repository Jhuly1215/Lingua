import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsentBase(BaseModel):
    """Atributos de consentimiento informado (patient_consents)."""
    consent_type: str = Field(..., min_length=1, max_length=50, description="Finalidad del consentimiento (ej. EVALUATION, RESEARCH, AUDIO_RECORDING)")
    consent_status: Literal["GRANTED", "DENIED", "WITHDRAWN"] = Field(..., description="Estado del consentimiento")
    consent_date: datetime = Field(..., description="Fecha y hora en que se otorgó o modificó el consentimiento")
    version: str = Field(default="1.0", min_length=1, max_length=50, description="Versión del documento de consentimiento informado")
    notes: Optional[str] = Field(None, description="Observaciones o notas adicionales")

    @field_validator("consent_type")
    @classmethod
    def validate_consent_type_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El tipo de consentimiento no puede estar vacío.")
        return v.strip()

    @field_validator("version")
    @classmethod
    def validate_version_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La versión del documento de consentimiento no puede estar vacía.")
        return v.strip()


class ConsentCreate(ConsentBase):
    """Esquema de entrada para registrar consentimiento."""
    pass


class ConsentUpdate(BaseModel):
    """Esquema para actualización de consentimiento existente."""
    consent_status: Optional[Literal["GRANTED", "DENIED", "WITHDRAWN"]] = None
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    notes: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("version")
    @classmethod
    def validate_version_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("La versión del documento de consentimiento no puede estar vacía.")
        return v.strip() if v is not None else None


class ConsentResponse(ConsentBase):
    """Esquema de salida con trazabilidad."""
    consent_id: uuid.UUID
    patient_id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
