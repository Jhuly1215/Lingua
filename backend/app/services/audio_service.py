import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.db.models.pipeline import Audio
from app.repositories.audio_repository import AudioRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.schemas.audio import AudioResponse, AudioSignedUrlResponse
from app.services.storage_service import StorageService


class AudioService:
    """
    Servicio de gestión y persistencia de grabaciones de audio clínico (US-10).
    Conecta la capa de base de datos relacional (metadatos) con Supabase Storage (archivos binarios).
    """

    ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".webm", ".m4a", ".flac", ".aac"}
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB límite preventivo

    def __init__(
        self,
        session: AsyncSession,
        storage_service: Optional[StorageService] = None,
    ):
        self.session = session
        self.audio_repo = AudioRepository(session)
        self.eval_repo = EvaluationRepository(session)
        self.storage_service = storage_service or StorageService()

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitiza el nombre del archivo para evitar inyecciones de ruta o caracteres inválidos."""
        clean = re.sub(r"[^\w.\-_]", "_", filename.strip())
        return clean or "recording.wav"

    async def upload_audio(
        self,
        evaluation_id: uuid.UUID,
        file_name: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
        duration_seconds: Optional[Decimal] = None,
        response_id: Optional[uuid.UUID] = None,
        recorded_at: Optional[datetime] = None,
    ) -> AudioResponse:
        """
        Guarda el archivo de audio en Supabase Storage y registra sus metadatos técnicos y clínicos.
        Cumple los criterios de aceptación de US-10:
        - Audio guardado con metadatos (tamaño, formato, canales, sample_rate).
        - Duración precisa (extraída del archivo o provista por el frontend de grabación).
        - Referencia persistida a Storage y URL firmada para reproducción.
        """
        # 1. Validar existencia y vigencia de la evaluación clínica
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        # 2. Validar tamaño del archivo
        file_size = len(file_bytes)
        if file_size == 0:
            raise ValidationException("El archivo de audio está vacío (0 bytes).")
        if file_size > self.MAX_FILE_SIZE_BYTES:
            raise ValidationException(
                f"El archivo de audio ({file_size} bytes) excede el tamaño máximo permitido de 100MB."
            )

        # 3. Sanitizar nombre de archivo
        safe_filename = self._sanitize_filename(file_name)

        # 4. Inspeccionar metadatos técnicos (formato, mime, sample_rate, canales, duración)
        meta = self.storage_service.inspect_audio_metadata(
            file_bytes=file_bytes,
            original_filename=safe_filename,
            provided_mime_type=content_type,
        )

        # 5. Determinar duración precisa
        final_duration = Decimal("0.0000")
        if duration_seconds is not None and duration_seconds > 0:
            final_duration = Decimal(str(round(duration_seconds, 4)))
        elif meta.get("duration_seconds") is not None:
            final_duration = meta["duration_seconds"]

        # 6. Definir identificador y ruta jerárquica en Supabase Storage
        audio_id = uuid.uuid4()
        storage_file_path = f"evaluations/{evaluation_id}/{audio_id}_{safe_filename}"

        # 7. Subir archivo a Supabase Storage
        self.storage_service.upload_audio_file(
            file_path=storage_file_path,
            file_bytes=file_bytes,
            mime_type=meta["mime_type"],
        )

        # 8. Persistir entidad relacional en PostgreSQL
        audio_record = Audio(
            audio_id=audio_id,
            evaluation_id=evaluation_id,
            response_id=response_id,
            file_name=safe_filename,
            file_path=storage_file_path,
            file_format=meta["file_format"],
            mime_type=meta["mime_type"],
            file_size_bytes=meta["file_size_bytes"],
            duration_seconds=final_duration,
            sample_rate=meta.get("sample_rate"),
            channels=meta.get("channels"),
            recorded_at=recorded_at or datetime.now(timezone.utc),
        )

        saved = await self.audio_repo.create(audio_record)

        # 9. Generar URL firmada para reproducción inmediata
        signed_url = self.storage_service.create_signed_url(storage_file_path)

        res = AudioResponse.model_validate(saved)
        res.signed_url = signed_url
        return res

    async def list_evaluation_audios(
        self, evaluation_id: uuid.UUID
    ) -> List[AudioResponse]:
        """Lista todos los audios clínicos activos pertenecientes a una evaluación."""
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        audios = await self.audio_repo.list_by_evaluation_id(evaluation_id, only_active=True)
        result: List[AudioResponse] = []
        for a in audios:
            resp = AudioResponse.model_validate(a)
            resp.signed_url = self.storage_service.create_signed_url(a.file_path)
            result.append(resp)
        return result

    async def get_audio_detail(
        self, evaluation_id: uuid.UUID, audio_id: uuid.UUID
    ) -> AudioResponse:
        """Obtiene el detalle y metadatos de un audio con su URL firmada."""
        audio = await self.audio_repo.get_by_evaluation_and_id(
            evaluation_id, audio_id, only_active=True
        )
        if not audio:
            raise EntityNotFoundException("Audio", audio_id)

        resp = AudioResponse.model_validate(audio)
        resp.signed_url = self.storage_service.create_signed_url(audio.file_path)
        return resp

    async def get_signed_playback_url(
        self, evaluation_id: uuid.UUID, audio_id: uuid.UUID, expires_in_seconds: int = 3600
    ) -> AudioSignedUrlResponse:
        """Genera una URL firmada de duración configurable para streaming o descarga segura."""
        audio = await self.audio_repo.get_by_evaluation_and_id(
            evaluation_id, audio_id, only_active=True
        )
        if not audio:
            raise EntityNotFoundException("Audio", audio_id)

        signed_url = self.storage_service.create_signed_url(
            audio.file_path, expires_in_seconds=expires_in_seconds
        )
        return AudioSignedUrlResponse(
            audio_id=audio.audio_id,
            file_name=audio.file_name,
            file_path=audio.file_path,
            signed_url=signed_url,
            expires_in_seconds=expires_in_seconds,
        )

    async def delete_audio(
        self, evaluation_id: uuid.UUID, audio_id: uuid.UUID
    ) -> None:
        """Realiza el borrado lógico del registro de audio conservando trazabilidad."""
        audio = await self.audio_repo.get_by_evaluation_and_id(
            evaluation_id, audio_id, only_active=True
        )
        if not audio:
            raise EntityNotFoundException("Audio", audio_id)

        await self.audio_repo.logical_delete(audio)

