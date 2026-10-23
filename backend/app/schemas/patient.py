import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    """Atributos comunes del paciente según el diccionario de datos v0.2."""
    patient_code: str = Field(..., min_length=2, max_length=50, description="Código clínico o identificador interno único")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date = Field(..., description="Fecha de nacimiento")
    gender: Optional[str] = Field(None, max_length=30, description="Sexo o género registrado")
    education_years: Optional[int] = Field(None, ge=0, description="Años de escolaridad acumulados")
    occupation: Optional[str] = Field(None, max_length=150)
    handedness: Optional[str] = Field(None, max_length=30, description="Lateralidad manual (diestro, zurdo, ambidiestro)")
    primary_language: str = Field(default="Español", max_length=100)
    bilingual: bool = Field(default=False)
    secondary_language: Optional[str] = Field(None, max_length=100)
    dialect_region: Optional[str] = Field(None, max_length=100, description="Variante o región dialectal relevante")
    medical_record_number: Optional[str] = Field(None, max_length=100, description="Número de historia clínica externa")
    clinical_background: Optional[str] = Field(None, description="Antecedentes clínicos y comorbilidades")
    notes: Optional[str] = Field(None, description="Observaciones generales")


class PatientCreate(PatientBase):
    """Esquema de entrada para registrar un nuevo paciente."""
    pass


class PatientUpdate(BaseModel):
    """Esquema para actualización parcial (PATCH) de datos permitidos del paciente."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=30)
    education_years: Optional[int] = Field(None, ge=0)
    occupation: Optional[str] = Field(None, max_length=150)
    handedness: Optional[str] = Field(None, max_length=30)
    primary_language: Optional[str] = Field(None, max_length=100)
    bilingual: Optional[bool] = None
    secondary_language: Optional[str] = Field(None, max_length=100)
    dialect_region: Optional[str] = Field(None, max_length=100)
    medical_record_number: Optional[str] = Field(None, max_length=100)
    clinical_background: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class PatientResponse(PatientBase):
    """Esquema de salida completo con identificadores y trazabilidad."""
    patient_id: uuid.UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
