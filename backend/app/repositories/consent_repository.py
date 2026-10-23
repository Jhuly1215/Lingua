import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.consent import PatientConsent
from app.repositories.base import BaseRepository


class ConsentRepository(BaseRepository[PatientConsent]):
    """Repositorio para la trazabilidad y consulta de consentimientos del paciente."""

    def __init__(self, session: AsyncSession):
        super().__init__(PatientConsent, session)

    async def list_by_patient_id(self, patient_id: uuid.UUID, only_active: bool = True) -> List[PatientConsent]:
        """Obtiene el historial de consentimientos registrados para un paciente."""
        stmt = select(PatientConsent).where(PatientConsent.patient_id == patient_id)
        if only_active:
            stmt = stmt.where(PatientConsent.active == True)
        stmt = stmt.order_by(PatientConsent.consent_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
