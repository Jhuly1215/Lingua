import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ClinicalEventBase(BaseModel):
    """Atributos de eventos clínicos neurológicos."""
    event_type: str = Field(..., max_length=100, description="Tipo de evento neurológico (ej. ACV Isquémico, ACV Hemorrágico, TCE)")
    event_date: date = Field(..., description="Fecha de ocurrencia del evento clínico")
    description: Optional[str] = Field(None, description="Descripción detallada del evento y cuadro agudo")
    event_severity: Optional[str] = Field(None, max_length=50, description="Severidad intrínseca del evento (Leve, Moderada, Severa, Crítica)")
    lesion_location: Optional[str] = Field(None, max_length=150, description="Localización neuroanatómica de la lesión")
    lesion_hemisphere: Optional[str] = Field(None, max_length=30, description="Hemisferio de la lesión (Izquierdo, Derecho, Bilateral)")


class ClinicalEventCreate(ClinicalEventBase):
    """Esquema para registrar un nuevo evento clínico."""
    pass


class ClinicalEventUpdate(BaseModel):
    """Esquema de actualización para eventos clínicos."""
    event_type: Optional[str] = Field(None, max_length=100)
    event_date: Optional[date] = None
    description: Optional[str] = None
    event_severity: Optional[str] = Field(None, max_length=50)
    lesion_location: Optional[str] = Field(None, max_length=150)
    lesion_hemisphere: Optional[str] = Field(None, max_length=30)
    active: Optional[bool] = None


class ClinicalEventResponse(ClinicalEventBase):
    """Respuesta con identificador y marcas temporales."""
    clinical_event_id: uuid.UUID
    patient_id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
