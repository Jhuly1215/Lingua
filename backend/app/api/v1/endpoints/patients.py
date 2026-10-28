import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.dependencies.auth import get_current_user, require_professional_or_admin
from app.dependencies.database import get_db
from app.schemas.clinical_event import (
    ClinicalEventCreate,
    ClinicalEventResponse,
    ClinicalEventUpdate,
)
from app.schemas.common import PaginatedResponse
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentUpdate
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.clinical_event_service import ClinicalEventService
from app.services.consent_service import ConsentService
from app.services.evaluation_service import EvaluationService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Pacientes"])


@router.get(
    "",
    response_model=PaginatedResponse[PatientResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar pacientes con paginación y búsqueda",
    description="Permite buscar pacientes por código clínico interno, nombre o apellido. Exige rol profesional o admin.",
)
async def list_patients(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda (código clínico, nombre)"),
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PatientResponse]:
    service = PatientService(session)
    return await service.list_patients(page=page, size=size, search=search)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo paciente",
    description="Crea la ficha de un paciente con sus variables sociolingüísticas y clínicas básicas.",
)
async def create_patient(
    data: PatientCreate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> PatientResponse:
    service = PatientService(session)
    return await service.create_patient(data)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar un paciente por UUID",
)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> PatientResponse:
    service = PatientService(session)
    return await service.get_patient_by_id(patient_id)


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de un paciente",
)
async def update_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> PatientResponse:
    service = PatientService(session)
    return await service.update_patient(patient_id, data)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminación lógica de un paciente",
    description="Cambia el estado lógico del paciente a inactivo para preservar la trazabilidad clínica.",
)
async def delete_patient(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = PatientService(session)
    await service.delete_patient(patient_id)


# --- Sub-recursos de Paciente: Eventos Clínicos (US-03) ---

@router.get(
    "/{patient_id}/clinical-events",
    response_model=List[ClinicalEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar eventos neurológicos del paciente",
)
async def list_patient_clinical_events(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[ClinicalEventResponse]:
    service = ClinicalEventService(session)
    return await service.list_events_by_patient(patient_id)


@router.post(
    "/{patient_id}/clinical-events",
    response_model=ClinicalEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un evento clínico para el paciente",
)
async def create_patient_clinical_event(
    patient_id: uuid.UUID,
    data: ClinicalEventCreate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ClinicalEventResponse:
    service = ClinicalEventService(session)
    return await service.create_event(patient_id, data)


@router.get(
    "/{patient_id}/clinical-events/{clinical_event_id}",
    response_model=ClinicalEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar un evento clínico específico del paciente",
)
async def get_patient_clinical_event(
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ClinicalEventResponse:
    service = ClinicalEventService(session)
    return await service.get_event_by_id(patient_id, clinical_event_id)


@router.patch(
    "/{patient_id}/clinical-events/{clinical_event_id}",
    response_model=ClinicalEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un evento clínico de un paciente",
)
async def update_patient_clinical_event(
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    data: ClinicalEventUpdate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ClinicalEventResponse:
    service = ClinicalEventService(session)
    return await service.update_event(patient_id, clinical_event_id, data)


# --- Sub-recursos de Paciente: Consentimiento Informado (US-04) ---

@router.get(
    "/{patient_id}/consents",
    response_model=List[ConsentResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar historial de consentimientos del paciente",
)
async def list_patient_consents(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[ConsentResponse]:
    service = ConsentService(session)
    return await service.list_consents_by_patient(patient_id)


@router.post(
    "/{patient_id}/consents",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un consentimiento informado",
)
async def create_patient_consent(
    patient_id: uuid.UUID,
    data: ConsentCreate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    service = ConsentService(session)
    return await service.create_consent(patient_id, data)


@router.get(
    "/{patient_id}/consents/{consent_id}",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar un consentimiento específico del paciente",
)
async def get_patient_consent(
    patient_id: uuid.UUID,
    consent_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    service = ConsentService(session)
    return await service.get_consent_by_id(patient_id, consent_id)


@router.patch(
    "/{patient_id}/consents/{consent_id}",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un consentimiento específico del paciente",
)
async def update_patient_consent(
    patient_id: uuid.UUID,
    consent_id: uuid.UUID,
    data: ConsentUpdate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    service = ConsentService(session)
    return await service.update_consent(patient_id, consent_id, data)


# --- Sub-recursos de Paciente: Evaluaciones (US-05) ---

@router.get(
    "/{patient_id}/evaluations",
    response_model=List[EvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar evaluaciones administradas a un paciente",
)
async def list_patient_evaluations(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[EvaluationResponse]:
    service = EvaluationService(session)
    return await service.list_evaluations_by_patient(patient_id)


@router.post(
    "/{patient_id}/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una evaluación para un paciente",
    description="Inicia una evaluación vinculando el paciente, protocolo y usuario evaluador autenticado.",
)
async def create_patient_evaluation(
    patient_id: uuid.UUID,
    data: EvaluationCreate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    service = EvaluationService(session)
    return await service.create_evaluation(
        patient_id=patient_id,
        evaluator_id=current_user.user_id,
        data=data,
    )
