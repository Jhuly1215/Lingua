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
from app.schemas.response import (
    FASConditionResponsesCreate,
    FASConditionScoreResponse,
    FASEvaluationSummaryResponse,
    ResponseResponse,
)
from app.services.evaluation_service import EvaluationService
from app.services.fas_scoring_service import FASScoringService

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


# --- Puntuación FAS y Registro de Respuestas (US-09) ---

@router.post(
    "/{evaluation_id}/subtests/{subtest_id}/responses",
    response_model=FASConditionScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar respuestas y obtener puntuación de una condición FAS (US-09)",
    description=(
        "Registra en lote las respuestas del paciente para una condición FAS (ej. F, A, S o Animales). "
        "Calcula el conteo de respuestas válidas y actualiza el score oficial en evaluation_subtests. "
        "Criterio de aceptación: Las repeticiones e intrusiones no suman al puntaje, pero se conservan para investigación."
    ),
)
async def record_condition_responses(
    evaluation_id: uuid.UUID,
    subtest_id: uuid.UUID,
    data: FASConditionResponsesCreate,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> FASConditionScoreResponse:
    service = FASScoringService(session)
    return await service.record_condition_responses(evaluation_id, subtest_id, data)


@router.get(
    "/{evaluation_id}/subtests/{subtest_id}/score",
    response_model=FASConditionScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener puntuación y desglose clínico de una condición FAS (US-09)",
    description=(
        "Obtiene el conteo de respuestas válidas de la condición y el desglose de errores conservados "
        "(perseveraciones, intrusiones fonéticas/semánticas, neologismos, etc.)."
    ),
)
async def get_condition_score(
    evaluation_id: uuid.UUID,
    subtest_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> FASConditionScoreResponse:
    service = FASScoringService(session)
    return await service.get_condition_score(evaluation_id, subtest_id)


@router.get(
    "/{evaluation_id}/fas-score",
    response_model=FASEvaluationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener resumen consolidado de puntuación FAS para la evaluación (US-09)",
    description=(
        "Calcula la puntuación fonética acumulada (F + A + S), la semántica y el total general FAS, "
        "junto con los totales consolidados de perseveraciones e intrusiones."
    ),
)
async def get_evaluation_fas_summary(
    evaluation_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> FASEvaluationSummaryResponse:
    service = FASScoringService(session)
    return await service.get_evaluation_fas_summary(evaluation_id)


@router.get(
    "/{evaluation_id}/responses",
    response_model=List[ResponseResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las respuestas registradas para una evaluación",
)
async def list_evaluation_responses(
    evaluation_id: uuid.UUID,
    current_user: User = Depends(require_professional_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[ResponseResponse]:
    service = FASScoringService(session)
    return await service.list_evaluation_responses(evaluation_id)
