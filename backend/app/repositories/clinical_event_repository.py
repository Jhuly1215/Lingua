import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clinical_event import ClinicalEvent
from app.repositories.base import BaseRepository


class ClinicalEventRepository(BaseRepository[ClinicalEvent]):
    """Repositorio para eventos clínicos neurológicos del paciente."""

    def __init__(self, session: AsyncSession):
        super().__init__(ClinicalEvent, session)

    async def list_by_patient_id(self, patient_id: uuid.UUID, only_active: bool = True) -> List[ClinicalEvent]:
        """Obtiene la lista cronológica de eventos clínicos asociados a un paciente."""
        stmt = select(ClinicalEvent).where(ClinicalEvent.patient_id == patient_id)
        if only_active:
            stmt = stmt.where(ClinicalEvent.active == True)
        stmt = stmt.order_by(ClinicalEvent.event_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
