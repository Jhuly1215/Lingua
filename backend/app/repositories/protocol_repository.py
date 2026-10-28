import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalogs import AphasiaType, SeverityLevel
from app.db.models.protocol import Protocol
from app.db.models.subtest import Subtest
from app.repositories.base import BaseRepository


class ProtocolRepository(BaseRepository[Protocol]):
    """Repositorio para protocolos clínicos, subpruebas y catálogos diagnósticos."""

    def __init__(self, session: AsyncSession):
        super().__init__(Protocol, session)

    async def get_protocol_with_subtests(self, protocol_id: uuid.UUID) -> Optional[Protocol]:
        """Obtiene un protocolo cargando sus subpruebas asociadas y activas."""
        stmt = (
            select(Protocol)
            .options(
                selectinload(Protocol.subtests).selectinload(Subtest.protocol)
            )
            .where(Protocol.protocol_id == protocol_id, Protocol.active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_subtests_by_protocol(self, protocol_id: uuid.UUID) -> List[Subtest]:
        """Lista las subpruebas pertenecientes a un protocolo específico ordenadas por order_number."""
        stmt = (
            select(Subtest)
            .where(Subtest.protocol_id == protocol_id, Subtest.active == True)
            .order_by(Subtest.order_number.asc().nulls_last())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_subtest_by_id(self, subtest_id: uuid.UUID) -> Optional[Subtest]:
        """Busca una subprueba por su ID."""
        stmt = select(Subtest).where(Subtest.subtest_id == subtest_id, Subtest.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_aphasia_types(self) -> List[AphasiaType]:
        """Lista el catálogo clínico de afasias."""
        stmt = select(AphasiaType).where(AphasiaType.active == True).order_by(AphasiaType.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_aphasia_type_by_id(self, aphasia_type_id: uuid.UUID) -> Optional[AphasiaType]:
        """Busca un tipo de afasia por su identificador único."""
        stmt = select(AphasiaType).where(AphasiaType.aphasia_type_id == aphasia_type_id, AphasiaType.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_severity_levels(self) -> List[SeverityLevel]:
        """Lista el catálogo de niveles de severidad."""
        stmt = select(SeverityLevel).where(SeverityLevel.active == True).order_by(SeverityLevel.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_severity_level_by_id(self, severity_level_id: uuid.UUID) -> Optional[SeverityLevel]:
        """Busca un nivel de severidad por su identificador único."""
        stmt = select(SeverityLevel).where(SeverityLevel.severity_level_id == severity_level_id, SeverityLevel.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()
