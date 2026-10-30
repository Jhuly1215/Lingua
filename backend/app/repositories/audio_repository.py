import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pipeline import Audio
from app.repositories.base import BaseRepository


class AudioRepository(BaseRepository[Audio]):
    """Repositorio para metadatos de grabaciones de audio clínico (US-10)."""

    def __init__(self, session: AsyncSession):
        super().__init__(Audio, session)

    async def list_by_evaluation_id(
        self, evaluation_id: uuid.UUID, only_active: bool = True
    ) -> List[Audio]:
        """Obtiene la lista de audios asociados a una evaluación clínica."""
        stmt = select(Audio).where(Audio.evaluation_id == evaluation_id)
        if only_active:
            stmt = stmt.where(Audio.active == True)
        stmt = stmt.order_by(Audio.recorded_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_evaluation_and_id(
        self, evaluation_id: uuid.UUID, audio_id: uuid.UUID, only_active: bool = True
    ) -> Optional[Audio]:
        """Obtiene un audio específico verificando que pertenezca a la evaluación."""
        stmt = select(Audio).where(
            Audio.audio_id == audio_id,
            Audio.evaluation_id == evaluation_id,
        )
        if only_active:
            stmt = stmt.where(Audio.active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
