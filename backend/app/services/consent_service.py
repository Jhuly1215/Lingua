import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.db.models.consent import PatientConsent
from app.repositories.consent_repository import ConsentRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentUpdate


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
        """Registra un nuevo consentimiento para un paciente conservando el historial."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        if data.consent_status not in ("GRANTED", "DENIED", "WITHDRAWN"):
            raise ValidationException(
                f"Estado de consentimiento inválido: '{data.consent_status}'. Debe ser GRANTED, DENIED o WITHDRAWN."
            )

        if not data.version or not data.version.strip():
            raise ValidationException("La versión del consentimiento informado es obligatoria.")

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
        """Obtiene el historial cronológico de consentimientos registrados para el paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        consents = await self.consent_repo.list_by_patient_id(patient_id, only_active=True)
        return [ConsentResponse.model_validate(c) for c in consents]

    async def get_consent_by_id(
        self,
        patient_id: uuid.UUID,
        consent_id: uuid.UUID,
    ) -> ConsentResponse:
        """Consulta un consentimiento específico de un paciente por su UUID."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        consent = await self.consent_repo.get_by_id(consent_id, only_active=True)
        if not consent or consent.patient_id != patient_id:
            raise EntityNotFoundException("Consentimiento", consent_id)

        return ConsentResponse.model_validate(consent)

    async def update_consent(
        self,
        patient_id: uuid.UUID,
        consent_id: uuid.UUID,
        data: ConsentUpdate,
    ) -> ConsentResponse:
        """Actualiza un consentimiento específico validando estado y pertenencia al paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        consent = await self.consent_repo.get_by_id(consent_id, only_active=True)
        if not consent or consent.patient_id != patient_id:
            raise EntityNotFoundException("Consentimiento", consent_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "consent_status" in update_dict and update_dict["consent_status"] not in ("GRANTED", "DENIED", "WITHDRAWN"):
            raise ValidationException(
                f"Estado de consentimiento inválido: '{update_dict['consent_status']}'. Debe ser GRANTED, DENIED o WITHDRAWN."
            )

        if "version" in update_dict and update_dict["version"] is not None:
            if not update_dict["version"].strip():
                raise ValidationException("La versión del consentimiento no puede estar vacía.")
            update_dict["version"] = update_dict["version"].strip()

        if "notes" in update_dict and isinstance(update_dict["notes"], str):
            update_dict["notes"] = update_dict["notes"].strip()

        updated_consent = await self.consent_repo.update(consent, update_dict)
        return ConsentResponse.model_validate(updated_consent)

    async def is_consent_granted(
        self,
        patient_id: uuid.UUID,
        consent_type: str,
    ) -> bool:
        """
        Verifica si el paciente cuenta actualmente con consentimiento otorgado ('GRANTED')
        para una finalidad determinada, evaluando el registro activo más reciente.
        Un estado 'DENIED' o 'WITHDRAWN' retorna estrictamente False.
        """
        consents = await self.consent_repo.list_by_patient_id(patient_id, only_active=True)
        # Filtrar por tipo de consentimiento
        matching = [c for c in consents if c.consent_type == consent_type.strip()]
        if not matching:
            return False

        # El más reciente (list_by_patient_id ya ordena por consent_date.desc())
        latest = matching[0]
        return latest.consent_status == "GRANTED"
