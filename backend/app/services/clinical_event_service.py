import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.db.models.clinical_event import ClinicalEvent
from app.repositories.clinical_event_repository import ClinicalEventRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.clinical_event import ClinicalEventCreate, ClinicalEventResponse, ClinicalEventUpdate


class ClinicalEventService:
    """
    Lógica de negocio para el registro, consulta y actualización de eventos clínicos neurológicos (US-03).
    Diferencia severidad del evento y ubicación de la lesión.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_repo = ClinicalEventRepository(session)
        self.patient_repo = PatientRepository(session)

    async def create_event(
        self,
        patient_id: uuid.UUID,
        data: ClinicalEventCreate,
    ) -> ClinicalEventResponse:
        """Registra un evento neurológico validando existencia del paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        event_obj = ClinicalEvent(
            clinical_event_id=uuid.uuid4(),
            patient_id=patient_id,
            event_type=data.event_type.strip(),
            event_date=data.event_date,
            description=data.description.strip() if data.description else None,
            event_severity=data.event_severity.strip() if data.event_severity else None,
            lesion_location=data.lesion_location.strip() if data.lesion_location else None,
            lesion_hemisphere=data.lesion_hemisphere.strip() if data.lesion_hemisphere else None,
        )

        saved_event = await self.event_repo.create(event_obj)
        return ClinicalEventResponse.model_validate(saved_event)

    async def list_events_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> List[ClinicalEventResponse]:
        """Obtiene todos los eventos clínicos asociados a un paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        events = await self.event_repo.list_by_patient_id(patient_id, only_active=True)
        return [ClinicalEventResponse.model_validate(e) for e in events]

    async def get_event_by_id(
        self,
        patient_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> ClinicalEventResponse:
        """Consulta un evento clínico específico asegurando pertenencia al paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        event = await self.event_repo.get_by_id(event_id, only_active=True)
        if not event or event.patient_id != patient_id:
            raise EntityNotFoundException("Evento clínico", event_id)

        return ClinicalEventResponse.model_validate(event)

    async def update_event(
        self,
        patient_id: uuid.UUID,
        event_id: uuid.UUID,
        data: ClinicalEventUpdate,
    ) -> ClinicalEventResponse:
        """Actualiza variables de un evento neurológico preservando la integridad."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        event = await self.event_repo.get_by_id(event_id, only_active=True)
        if not event or event.patient_id != patient_id:
            raise EntityNotFoundException("Evento clínico", event_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key in ["event_type", "description", "event_severity", "lesion_location", "lesion_hemisphere"]:
            if key in update_dict and isinstance(update_dict[key], str):
                update_dict[key] = update_dict[key].strip()

        updated_event = await self.event_repo.update(event, update_dict)
        return ClinicalEventResponse.model_validate(updated_event)
