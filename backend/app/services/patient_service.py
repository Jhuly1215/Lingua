import math
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityConflictException, EntityNotFoundException, ValidationException
from app.db.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.common import PaginatedResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate


class PatientService:
    """
    Lógica de negocio para el registro, consulta y actualización de pacientes (US-02 y US-03).
    Garantiza unicidad de códigos, validaciones de variables clínicas y borrado lógico.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.patient_repo = PatientRepository(session)

    async def create_patient(self, data: PatientCreate) -> PatientResponse:
        """Registra un nuevo paciente validando código clínico y reglas de negocio."""
        # Validar si ya existe un paciente con ese código clínico interno
        existing = await self.patient_repo.get_by_code(data.patient_code, only_active=False)
        if existing:
            raise EntityConflictException(
                f"Ya existe un paciente registrado con el código clínico '{data.patient_code}'."
            )

        if data.education_years is not None and data.education_years < 0:
            raise ValidationException("Los años de escolaridad no pueden ser un valor negativo.")

        patient_obj = Patient(
            patient_id=uuid.uuid4(),
            patient_code=data.patient_code.strip(),
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            date_of_birth=data.date_of_birth,
            gender=data.gender.strip() if data.gender else None,
            education_years=data.education_years,
            occupation=data.occupation.strip() if data.occupation else None,
            handedness=data.handedness.strip() if data.handedness else None,
            primary_language=data.primary_language.strip(),
            bilingual=data.bilingual,
            secondary_language=data.secondary_language.strip() if data.secondary_language else None,
            dialect_region=data.dialect_region.strip() if data.dialect_region else None,
            medical_record_number=data.medical_record_number.strip() if data.medical_record_number else None,
            clinical_background=data.clinical_background.strip() if data.clinical_background else None,
            notes=data.notes.strip() if data.notes else None,
        )

        saved_patient = await self.patient_repo.create(patient_obj)
        return PatientResponse.model_validate(saved_patient)

    async def get_patient_by_id(self, patient_id: uuid.UUID) -> PatientResponse:
        """Obtiene un paciente por su UUID primario."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)
        return PatientResponse.model_validate(patient)

    async def get_patient_entity(self, patient_id: uuid.UUID) -> Patient:
        """Obtiene la entidad ORM del paciente validando existencia y estado activo."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)
        return patient

    async def list_patients(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
    ) -> PaginatedResponse[PatientResponse]:
        """Lista pacientes con paginación y búsqueda segura."""
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 20

        skip = (page - 1) * size
        patients, total = await self.patient_repo.list_paginated_and_search(
            skip=skip,
            limit=size,
            query=search,
            only_active=True,
        )

        pages = math.ceil(total / size) if total > 0 else 0
        items = [PatientResponse.model_validate(p) for p in patients]

        return PaginatedResponse[PatientResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update_patient(self, patient_id: uuid.UUID, data: PatientUpdate) -> PatientResponse:
        """Actualiza parcialmente los datos permitidos de un paciente."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)

        update_dict = data.model_dump(exclude_unset=True)

        if "education_years" in update_dict and update_dict["education_years"] is not None:
            if update_dict["education_years"] < 0:
                raise ValidationException("Los años de escolaridad no pueden ser un valor negativo.")

        updated_patient = await self.patient_repo.update(patient, update_dict)
        return PatientResponse.model_validate(updated_patient)

    async def delete_patient(self, patient_id: uuid.UUID) -> None:
        """Aplica eliminación lógica al paciente sin pérdida física de trazabilidad."""
        patient = await self.patient_repo.get_by_id(patient_id, only_active=True)
        if not patient:
            raise EntityNotFoundException("Paciente", patient_id)
        await self.patient_repo.logical_delete(patient)
