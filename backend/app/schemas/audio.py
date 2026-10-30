import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AudioResponse(BaseModel):
    """
    Esquema de salida para metadatos de audio clínico (US-10).
    Representa una fila de la tabla relacional 'audio' y su referencia a Storage.
    """
    audio_id: uuid.UUID = Field(..., description="Identificador único del archivo de audio")
    evaluation_id: uuid.UUID = Field(..., description="Evaluación clínica a la que pertenece")
    response_id: Optional[uuid.UUID] = Field(None, description="Respuesta específica asociada, si aplica")
    file_name: str = Field(..., description="Nombre original del archivo de audio")
    file_path: str = Field(..., description="Ruta relativa del objeto dentro de Supabase Storage")
    file_format: str = Field(..., description="Formato o extensión del audio (ej. wav, mp3, webm)")
    mime_type: str = Field(..., description="Tipo MIME del archivo (ej. audio/wav)")
    file_size_bytes: int = Field(..., description="Tamaño del archivo en bytes")
    duration_seconds: Decimal = Field(..., description="Duración exacta en segundos con precisión decimal")
    sample_rate: Optional[int] = Field(None, description="Frecuencia de muestreo en Hz (ej. 16000, 44100)")
    channels: Optional[int] = Field(None, description="Cantidad de canales de audio (1=mono, 2=estéreo)")
    recorded_at: datetime = Field(..., description="Fecha y hora de grabación o carga del archivo")
    signed_url: Optional[str] = Field(None, description="URL firmada temporal para descarga o reproducción segura")
    active: bool = Field(True, description="Indicador de borrado lógico")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AudioSignedUrlResponse(BaseModel):
    """Respuesta que proporciona una URL firmada de corta duración para reproducción segura."""
    audio_id: uuid.UUID
    file_name: str
    file_path: str
    signed_url: str = Field(..., description="URL firmada con token para acceso temporal al audio")
    expires_in_seconds: int = Field(..., description="Segundos de validez de la URL firmada")


class AudioUploadResponse(BaseModel):
    """Respuesta tras completar exitosamente la carga de un archivo de audio."""
    message: str = "Audio cargado y registrado satisfactoriamente con sus metadatos."
    audio: AudioResponse
