import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.db.models.consent import PatientConsent
from app.repositories.consent_repository import ConsentRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.consent import ConsentCreate, ConsentResponse


class ConsentService:
    """
    Lógica de negocio para la gestión del consentimiento informado (US-04).
    Mantiene trazabilidad estricta y evita sobreescritura silenciosa de consentimientos.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.consent_repo = ConsentRepository(session)
        self.patient_repo = PatientRepository(session)

    async def create_consent(
        self,
        patient_id: uuid.UUID,
        data: ConsentCreate,
    ) -> ConsentResponse:
        """Registra un nuevo consentimiento para un paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        if data.consent_status not in ("GRANTED", "DENIED", "WITHDRAWN"):
            raise ValidationException(
                f"Estado de consentimiento inválido: '{data.consent_status}'. Debe ser GRANTED, DENIED o WITHDRAWN."
            )

        consent_obj = PatientConsent(
            consent_id=uuid.uuid4(),
            patient_id=patient_id,
            consent_type=data.consent_type.strip(),
            consent_status=data.consent_status,
            consent_date=data.consent_date,
            version=data.version.strip(),
            notes=data.notes.strip() if data.notes else None,
        )

        saved_consent = await self.consent_repo.create(consent_obj)
        return ConsentResponse.model_validate(saved_consent)

    async def list_consents_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> List[ConsentResponse]:
        """Obtiene el historial de consentimientos registrados para el paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        consents = await self.consent_repo.list_by_patient_id(patient_id, only_active=True)
        return [ConsentResponse.model_validate(c) for c in consents]
