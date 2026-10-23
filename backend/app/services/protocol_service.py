import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.repositories.protocol_repository import ProtocolRepository
from app.schemas.protocol import (
    AphasiaTypeResponse,
    ProtocolDetailResponse,
    ProtocolResponse,
    SeverityLevelResponse,
    SubtestResponse,
)


class ProtocolService:
    """
    Lógica de negocio para protocolos, subpruebas y catálogos clínicos (US-06).
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.protocol_repo = ProtocolRepository(session)

    async def list_protocols(self) -> List[ProtocolResponse]:
        """Lista todos los protocolos de evaluación activos."""
        protocols = await self.protocol_repo.list(only_active=True)
        return [ProtocolResponse.model_validate(p) for p in protocols]

    async def get_protocol_detail(self, protocol_id: uuid.UUID) -> ProtocolDetailResponse:
        """Obtiene un protocolo con sus subpruebas ordenadas."""
        protocol = await self.protocol_repo.get_protocol_with_subtests(protocol_id)
        if not protocol:
            raise EntityNotFoundException("Protocolo", protocol_id)
        return ProtocolDetailResponse.model_validate(protocol)

    async def list_subtests_by_protocol(self, protocol_id: uuid.UUID) -> List[SubtestResponse]:
        """Lista las subpruebas pertenecientes a un protocolo específico."""
        protocol = await self.protocol_repo.get_by_id(protocol_id, only_active=True)
        if not protocol:
            raise EntityNotFoundException("Protocolo", protocol_id)

        subtests = await self.protocol_repo.list_subtests_by_protocol(protocol_id)
        return [SubtestResponse.model_validate(s) for s in subtests]

    async def list_aphasia_types(self) -> List[AphasiaTypeResponse]:
        """Consulta el catálogo clínico de afasias."""
        items = await self.protocol_repo.list_aphasia_types()
        return [AphasiaTypeResponse.model_validate(i) for i in items]

    async def list_severity_levels(self) -> List[SeverityLevelResponse]:
        """Consulta el catálogo de grados de severidad."""
        items = await self.protocol_repo.list_severity_levels()
        return [SeverityLevelResponse.model_validate(i) for i in items]
