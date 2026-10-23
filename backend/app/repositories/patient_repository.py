import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """Repositorio para la gestión de pacientes y variables clínicas."""

    def __init__(self, session: AsyncSession):
        super().__init__(Patient, session)

    async def get_by_code(self, patient_code: str, only_active: bool = True) -> Optional[Patient]:
        """Busca un paciente por su código clínico interno único."""
        stmt = select(Patient).where(Patient.patient_code == patient_code.strip())
        if only_active:
            stmt = stmt.where(Patient.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_paginated_and_search(
        self,
        skip: int = 0,
        limit: int = 20,
        query: Optional[str] = None,
        only_active: bool = True,
    ) -> Tuple[List[Patient], int]:
        """
        Lista pacientes con paginación y búsqueda flexible por código interno o nombres.
        Retorna la tupla (lista_pacientes, total_coincidencias).
        """
        stmt = select(Patient)
        count_stmt = select(func.count(Patient.patient_id))

        if only_active:
            stmt = stmt.where(Patient.active == True)
            count_stmt = count_stmt.where(Patient.active == True)

        if query:
            clean_query = f"%{query.strip().lower()}%"
            search_clause = or_(
                func.lower(Patient.patient_code).like(clean_query),
                func.lower(Patient.first_name).like(clean_query),
                func.lower(Patient.last_name).like(clean_query),
                func.lower(Patient.medical_record_number).like(clean_query),
            )
            stmt = stmt.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        # Contar total
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Obtener página ordenada
        stmt = stmt.order_by(Patient.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total
