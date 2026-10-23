import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.evaluation import Evaluation, EvaluationSubtest
from app.repositories.base import BaseRepository


class EvaluationRepository(BaseRepository[Evaluation]):
    """Repositorio para la administración y configuración de evaluaciones clínicas."""

    def __init__(self, session: AsyncSession):
        super().__init__(Evaluation, session)

    async def get_by_id_detailed(self, evaluation_id: uuid.UUID) -> Optional[Evaluation]:
        """Obtiene la evaluación cargando subpruebas aplicadas y detalles."""
        stmt = (
            select(Evaluation)
            .options(
                selectinload(Evaluation.evaluation_subtests).selectinload(EvaluationSubtest.subtest),
                selectinload(Evaluation.patient),
                selectinload(Evaluation.protocol),
                selectinload(Evaluation.evaluator),
            )
            .where(Evaluation.evaluation_id == evaluation_id, Evaluation.active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_by_patient_id(self, patient_id: uuid.UUID, only_active: bool = True) -> List[Evaluation]:
        """Lista cronológicamente las evaluaciones pertenecientes a un paciente."""
        stmt = select(Evaluation).where(Evaluation.patient_id == patient_id)
        if only_active:
            stmt = stmt.where(Evaluation.active == True)
        stmt = stmt.order_by(Evaluation.evaluation_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_subtest_association(
        self,
        evaluation_id: uuid.UUID,
        subtest_id: uuid.UUID,
    ) -> Optional[EvaluationSubtest]:
        """Verifica si una subprueba ya fue asociada previamente a la evaluación."""
        stmt = select(EvaluationSubtest).where(
            EvaluationSubtest.evaluation_id == evaluation_id,
            EvaluationSubtest.subtest_id == subtest_id,
            EvaluationSubtest.active == True,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_subtest_to_evaluation(
        self,
        association: EvaluationSubtest,
    ) -> EvaluationSubtest:
        """Asocia una subprueba a una evaluación."""
        self.session.add(association)
        await self.session.flush()
        await self.session.refresh(association)
        return association

    async def list_evaluation_subtests(
        self,
        evaluation_id: uuid.UUID,
    ) -> List[EvaluationSubtest]:
        """Lista todas las subpruebas asociadas a una evaluación."""
        stmt = (
            select(EvaluationSubtest)
            .options(selectinload(EvaluationSubtest.subtest))
            .where(
                EvaluationSubtest.evaluation_id == evaluation_id,
                EvaluationSubtest.active == True,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
