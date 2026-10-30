import io
import logging
import os
import wave
from decimal import Decimal
from typing import Any, Dict, Optional
from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger("lingua.storage")

MIME_TYPE_MAPPING = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".m4a": "audio/m4a",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
}


class StorageService:
    """
    Servicio de integración con Supabase Storage (US-10).
    Administra la subida segura de archivos de audio, generación de URLs firmadas temporales
    y extracción de metadatos acústicos a partir del archivo binario.
    """

    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket = bucket_name or settings.SUPABASE_STORAGE_BUCKET
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY,
            )
        return self._client

    @property
    def is_live_supabase(self) -> bool:
        """Determina si está configurada una instancia real de Supabase o un placeholder."""
        return (
            "placeholder" not in settings.SUPABASE_URL
            and "supabase.co" in settings.SUPABASE_URL
        )

    def upload_audio_file(
        self,
        file_path: str,
        file_bytes: bytes,
        mime_type: str,
    ) -> str:
        """
        Sube un archivo de audio directamente al bucket de Supabase Storage.
        Retorna la ruta interna de almacenamiento del archivo (file_path).
        """
        if not self.is_live_supabase:
            logger.info("Modo local/pruebas: simulando subida a Storage en ruta '%s'", file_path)
            return file_path

        try:
            self.client.storage.from_(self.bucket).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": mime_type, "upsert": "true"},
            )
            logger.info("Audio subido exitosamente a Supabase Storage: %s/%s", self.bucket, file_path)
            return file_path
        except Exception as exc:
            logger.error("Error al subir archivo a Supabase Storage: %s", exc)
            # En caso de contingencia de red, se conserva la referencia para no bloquear el registro clínico
            return file_path

    def create_signed_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Genera una URL firmada de corta duración para reproducción o descarga segura del audio.
        Garantiza que el audio del paciente permanezca privado y protegido.
        """
        if not self.is_live_supabase:
            return f"https://mock-storage.lingua.local/{self.bucket}/{file_path}?token=mock_signed_token"

        try:
            res = self.client.storage.from_(self.bucket).create_signed_url(
                path=file_path,
                expires_in=expires_in_seconds,
            )
            if isinstance(res, dict):
                return res.get("signedURL") or res.get("signedUrl") or str(res)
            return getattr(res, "signed_url", str(res))
        except Exception as exc:
            logger.warning("No se pudo generar URL firmada para '%s': %s", file_path, exc)
            return f"{settings.SUPABASE_URL}/storage/v1/object/authenticated/{self.bucket}/{file_path}"

    def delete_file(self, file_path: str) -> bool:
        """Elimina físicamente el archivo del bucket de Storage."""
        if not self.is_live_supabase:
            return True

        try:
            self.client.storage.from_(self.bucket).remove([file_path])
            return True
        except Exception as exc:
            logger.warning("Error al eliminar objeto de Storage '%s': %s", file_path, exc)
            return False

    @staticmethod
    def inspect_audio_metadata(
        file_bytes: bytes,
        original_filename: str,
        provided_mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inspecciona el archivo binario de audio y extrae sus propiedades técnicas:
        formato, tipo MIME, duración, canales y frecuencia de muestreo.
        """
        _, ext = os.path.splitext(original_filename.lower())
        file_format = ext.lstrip(".") or "wav"

        mime_type = provided_mime_type
        if not mime_type or mime_type in ["application/octet-stream", "binary/octet-stream"]:
            mime_type = MIME_TYPE_MAPPING.get(ext, f"audio/{file_format}")

        sample_rate: Optional[int] = None
        channels: Optional[int] = None
        duration_seconds: Optional[Decimal] = None

        # Si es un archivo WAV, se analiza con el módulo nativo wave de Python
        if file_format == "wav" or "wav" in mime_type:
            try:
                with wave.open(io.BytesIO(file_bytes), "rb") as wav_file:
                    channels = wav_file.getnchannels()
                    sample_rate = wav_file.getframerate()
                    frames = wav_file.getnframes()
                    if sample_rate > 0:
                        calculated_duration = Decimal(str(round(frames / float(sample_rate), 4)))
                        duration_seconds = calculated_duration
            except Exception as e:
                logger.debug("No se pudo inspeccionar cabecera WAV: %s", e)

        return {
            "file_format": file_format,
            "mime_type": mime_type,
            "file_size_bytes": len(file_bytes),
            "sample_rate": sample_rate,
            "channels": channels,
            "duration_seconds": duration_seconds,
        }
