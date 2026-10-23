import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.schemas.protocol import (
    AphasiaTypeResponse,
    ProtocolDetailResponse,
    ProtocolResponse,
    SeverityLevelResponse,
    SubtestResponse,
)
from app.services.protocol_service import ProtocolService

router = APIRouter(tags=["Protocolos y Catálogos Clínicos"])


@router.get(
    "/protocols",
    response_model=List[ProtocolResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar protocolos de evaluación disponibles",
)
async def list_protocols(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[ProtocolResponse]:
    service = ProtocolService(session)
    return await service.list_protocols()


@router.get(
    "/protocols/{protocol_id}",
    response_model=ProtocolDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar protocolo con sus subpruebas",
)
async def get_protocol(
    protocol_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProtocolDetailResponse:
    service = ProtocolService(session)
    return await service.get_protocol_detail(protocol_id)


@router.get(
    "/protocols/{protocol_id}/subtests",
    response_model=List[SubtestResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar subpruebas de un protocolo",
)
async def list_protocol_subtests(
    protocol_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[SubtestResponse]:
    service = ProtocolService(session)
    return await service.list_subtests_by_protocol(protocol_id)


# --- Catálogos clínicos adicionales ---

@router.get(
    "/catalogs/aphasia-types",
    response_model=List[AphasiaTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar catálogo de tipos de afasia",
    description="Incluye tipos clásicos, 'Mixta' y 'No clasificada' conforme al diccionario clínico.",
)
async def list_aphasia_types(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[AphasiaTypeResponse]:
    service = ProtocolService(session)
    return await service.list_aphasia_types()


@router.get(
    "/catalogs/severity-levels",
    response_model=List[SeverityLevelResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar catálogo de niveles de severidad",
)
async def list_severity_levels(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[SeverityLevelResponse]:
    service = ProtocolService(session)
    return await service.list_severity_levels()
