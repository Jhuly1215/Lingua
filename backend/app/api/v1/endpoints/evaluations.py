import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.dependencies.auth import require_professional_or_admin
from app.dependencies.database import get_db
from app.schemas.evaluation import (
    EvaluationDetailResponse,
    EvaluationResponse,
    EvaluationSubtestCreate,
    EvaluationSubtestResponse,
    EvaluationUpdate,
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["Evaluaciones"])


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de una evaluación por UUID",
    description="Devuelve la cabecera de la evaluación, metadatos del protocolo, evaluador y subpruebas configuradas.",
)
async def get_evaluation(
    evaluation_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> EvaluationDetailResponse:
    service = EvaluationService(session)
    return await service.get_evaluation_by_id(evaluation_id)


@router.patch(
    "/{evaluation_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar estado u observaciones de una evaluación",
)
async def update_evaluation(
    evaluation_id: uuid.UUID,
    data: EvaluationUpdate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    service = EvaluationService(session)
    return await service.update_evaluation(evaluation_id, data)


@router.get(
    "/{evaluation_id}/subtests",
    response_model=List[EvaluationSubtestResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar subpruebas configuradas para una evaluación",
)
async def list_evaluation_subtests(
    evaluation_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[EvaluationSubtestResponse]:
    service = EvaluationService(session)
    return await service.list_evaluation_subtests(evaluation_id)


@router.post(
    "/{evaluation_id}/subtests",
    response_model=EvaluationSubtestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asociar y configurar una subprueba en la evaluación (US-06)",
    description="Asocia una subprueba del protocolo a la evaluación, registrando duración aplicada (ej. FAS) y previniendo duplicados.",
)
async def add_subtest_to_evaluation(
    evaluation_id: uuid.UUID,
    data: EvaluationSubtestCreate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> EvaluationSubtestResponse:
    service = EvaluationService(session)
    return await service.add_subtest_to_evaluation(evaluation_id, data)
