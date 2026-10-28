import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pipeline import Item, Response
from app.repositories.base import BaseRepository


class ResponseRepository(BaseRepository[Response]):
    """
    Repositorio para el almacenamiento, consulta y trazabilidad de respuestas (responses)
    e ítems clínicos (items).
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Response, session)

    async def bulk_create(self, responses: List[Response]) -> List[Response]:
        """Inserta múltiples respuestas en bloque dentro de la sesión activa."""
        for resp in responses:
            self.session.add(resp)
        await self.session.flush()
        for resp in responses:
            await self.session.refresh(resp)
        return responses

    async def list_by_evaluation(
        self,
        evaluation_id: uuid.UUID,
        only_active: bool = True,
    ) -> List[Response]:
        """Recupera todas las respuestas de una evaluación ordenadas secuencialmente."""
        stmt = select(Response).where(Response.evaluation_id == evaluation_id)
        if only_active:
            stmt = stmt.where(Response.active == True)
        stmt = stmt.order_by(Response.response_order.asc(), Response.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_evaluation_and_subtest(
        self,
        evaluation_id: uuid.UUID,
        subtest_id: uuid.UUID,
        only_active: bool = True,
    ) -> List[Response]:
        """
        Recupera las respuestas de una condición/subprueba específica mediante el vínculo con Item.
        """
        stmt = (
            select(Response)
            .join(Item, Response.item_id == Item.item_id)
            .where(
                Response.evaluation_id == evaluation_id,
                Item.subtest_id == subtest_id,
            )
        )
        if only_active:
            stmt = stmt.where(Response.active == True, Item.active == True)
        stmt = stmt.order_by(Response.response_order.asc(), Response.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_or_create_subtest_item(
        self,
        subtest_id: uuid.UUID,
        item_code: Optional[str] = None,
        stimulus_text: Optional[str] = None,
        instruction_text: Optional[str] = None,
    ) -> Item:
        """
        Garantiza la existencia de un registro Item para la subprueba/condición clínica dada,
        permitiendo vincular foreign key `item_id` en las respuestas.
        """
        stmt = (
            select(Item)
            .where(Item.subtest_id == subtest_id, Item.active == True)
            .order_by(Item.item_number.asc())
        )
        result = await self.session.execute(stmt)
        item = result.scalars().first()
        if not item:
            item = Item(
                item_id=uuid.uuid4(),
                subtest_id=subtest_id,
                item_number=1,
                item_code=item_code or "FAS_COND_ITEM",
                stimulus_text=stimulus_text or "Estímulo de condición FAS",
                instruction_text=instruction_text,
                response_type="VERBAL_FLUENCY",
                order_number=1,
            )
            self.session.add(item)
            await self.session.flush()
            await self.session.refresh(item)
        return item
