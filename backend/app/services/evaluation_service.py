import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityConflictException, EntityNotFoundException, ValidationException
from app.db.models.evaluation import Evaluation, EvaluationSubtest
from app.repositories.clinical_event_repository import ClinicalEventRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.protocol_repository import ProtocolRepository
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationDetailResponse,
    EvaluationResponse,
    EvaluationSubtestCreate,
    EvaluationSubtestResponse,
    EvaluationUpdate,
)


class EvaluationService:
    """
    Lógica de negocio para sesiones de evaluación (US-05) y subpruebas (US-06).
    Asegura validación de pertenencia al protocolo, integridad referencial y prevención de duplicados.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.eval_repo = EvaluationRepository(session)
        self.patient_repo = PatientRepository(session)
        self.protocol_repo = ProtocolRepository(session)
        self.event_repo = ClinicalEventRepository(session)

    async def create_evaluation(
        self,
        patient_id: uuid.UUID,
        evaluator_id: uuid.UUID,
        data: EvaluationCreate,
    ) -> EvaluationResponse:
        """Crea una nueva evaluación para un paciente validando protocolo, evento clínico y catálogos."""
        # 1. Validar existencia y estado del paciente
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        # 2. Validar protocolo
        protocol = await self.protocol_repo.get_by_id(data.protocol_id, only_active=True)
        if not protocol:
            raise EntityNotFoundException("Protocolo", data.protocol_id)

        # 3. Validar evento clínico si fue proporcionado
        if data.clinical_event_id:
            event = await self.event_repo.get_by_id(data.clinical_event_id, only_active=True)
            if not event or event.patient_id != patient_id:
                raise ValidationException("El evento clínico proporcionado no existe o no pertenece a este paciente.")

        # 4. Validar tipo de afasia si fue proporcionado (permite None / no clasificada aún)
        if data.aphasia_type_id is not None:
            aphasia_type = await self.protocol_repo.get_aphasia_type_by_id(data.aphasia_type_id)
            if not aphasia_type:
                raise EntityNotFoundException("Tipo de afasia", data.aphasia_type_id)

        # 5. Validar nivel de severidad si fue proporcionado
        if data.severity_level_id is not None:
            severity = await self.protocol_repo.get_severity_level_by_id(data.severity_level_id)
            if not severity:
                raise EntityNotFoundException("Nivel de severidad", data.severity_level_id)

        eval_obj = Evaluation(
            evaluation_id=uuid.uuid4(),
            patient_id=patient_id,
            evaluator_id=evaluator_id,
            protocol_id=data.protocol_id,
            clinical_event_id=data.clinical_event_id,
            aphasia_type_id=data.aphasia_type_id,
            severity_level_id=data.severity_level_id,
            evaluation_date=data.evaluation_date,
            status=data.status or "PENDING",
            general_observations=data.general_observations.strip() if data.general_observations else None,
        )

        saved_eval = await self.eval_repo.create(eval_obj)
        return EvaluationResponse.model_validate(saved_eval)

    async def get_evaluation_by_id(self, evaluation_id: uuid.UUID) -> EvaluationDetailResponse:
        """Obtiene la evaluación completa con sus subpruebas asociadas y entidades contextuales."""
        evaluation = await self.eval_repo.get_by_id_detailed(evaluation_id)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)
        return EvaluationDetailResponse.model_validate(evaluation)

    async def list_evaluations_by_patient(self, patient_id: uuid.UUID) -> List[EvaluationResponse]:
        """Lista todas las evaluaciones administradas a un paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        evaluations = await self.eval_repo.list_by_patient_id(patient_id, only_active=True)
        return [EvaluationResponse.model_validate(e) for e in evaluations]

    async def update_evaluation(
        self,
        evaluation_id: uuid.UUID,
        data: EvaluationUpdate,
    ) -> EvaluationResponse:
        """Actualiza parcialmente los campos permitidos de una evaluación con validación de integridad."""
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        update_dict = data.model_dump(exclude_unset=True)

        if "clinical_event_id" in update_dict and update_dict["clinical_event_id"] is not None:
            event = await self.event_repo.get_by_id(update_dict["clinical_event_id"], only_active=True)
            if not event or event.patient_id != evaluation.patient_id:
                raise ValidationException("El evento clínico proporcionado no existe o no pertenece a este paciente.")

        if "aphasia_type_id" in update_dict and update_dict["aphasia_type_id"] is not None:
            aphasia_type = await self.protocol_repo.get_aphasia_type_by_id(update_dict["aphasia_type_id"])
            if not aphasia_type:
                raise EntityNotFoundException("Tipo de afasia", update_dict["aphasia_type_id"])

        if "severity_level_id" in update_dict and update_dict["severity_level_id"] is not None:
            severity = await self.protocol_repo.get_severity_level_by_id(update_dict["severity_level_id"])
            if not severity:
                raise EntityNotFoundException("Nivel de severidad", update_dict["severity_level_id"])

        if "general_observations" in update_dict and isinstance(update_dict["general_observations"], str):
            update_dict["general_observations"] = update_dict["general_observations"].strip()

        updated_eval = await self.eval_repo.update(evaluation, update_dict)
        return EvaluationResponse.model_validate(updated_eval)

    async def add_subtest_to_evaluation(
        self,
        evaluation_id: uuid.UUID,
        data: EvaluationSubtestCreate,
    ) -> EvaluationSubtestResponse:
        """
        Asocia una subprueba a la evaluación (US-06).
        Valida que la subprueba pertenezca al protocolo de la evaluación y evita duplicados.
        """
        # 1. Validar evaluación activa
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        # 2. Validar subprueba activa
        subtest = await self.protocol_repo.get_subtest_by_id(data.subtest_id)
        if not subtest:
            raise EntityNotFoundException("Subprueba", data.subtest_id)

        # 3. Validar que la subprueba pertenezca al protocolo de la evaluación
        if subtest.protocol_id != evaluation.protocol_id:
            raise ValidationException(
                f"La subprueba '{subtest.name}' (ID: {subtest.subtest_id}) no pertenece al protocolo asignado a esta evaluación."
            )

        # 4. Validar que no exista asociación duplicada
        existing = await self.eval_repo.get_subtest_association(evaluation_id, data.subtest_id)
        if existing:
            raise EntityConflictException(
                f"La subprueba '{subtest.name}' ya se encuentra asociada a esta evaluación."
            )

        # 5. Validar duración si se proporciona
        if data.duration_seconds is not None and data.duration_seconds <= 0:
            raise ValidationException("La duración de la subprueba debe ser un valor positivo mayor a 0 segundos.")

        subtest_assoc = EvaluationSubtest(
            evaluation_subtest_id=uuid.uuid4(),
            evaluation_id=evaluation_id,
            subtest_id=data.subtest_id,
            duration_seconds=data.duration_seconds,
            score=data.score,
            status=data.status or "PENDING",
            observations=data.observations.strip() if data.observations else None,
        )

        saved_assoc = await self.eval_repo.add_subtest_to_evaluation(subtest_assoc)
        saved_assoc.subtest = subtest
        return EvaluationSubtestResponse.model_validate(saved_assoc)

    async def list_evaluation_subtests(
        self,
        evaluation_id: uuid.UUID,
    ) -> List[EvaluationSubtestResponse]:
        """Lista todas las subpruebas asociadas a una evaluación."""
        evaluation = await self.eval_repo.get_by_id(evaluation_id, only_active=True)
        if not evaluation:
            raise EntityNotFoundException("Evaluación", evaluation_id)

        subtests = await self.eval_repo.list_evaluation_subtests(evaluation_id)
        return [EvaluationSubtestResponse.model_validate(s) for s in subtests]
