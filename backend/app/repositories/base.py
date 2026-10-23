import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repositorio base genérico para operaciones CRUD asíncronas con SQLAlchemy 2.x.
    Aplica por defecto el filtro de borrado lógico `active == True`.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Union[uuid.UUID, str], only_active: bool = True) -> Optional[ModelType]:
        """Obtiene un registro por su clave primaria."""
        # Identificar el nombre de la clave primaria del modelo (ej. patient_id, user_id, etc.)
        pk_col = list(self.model.__table__.primary_key.columns)[0]
        stmt = select(self.model).where(pk_col == id_val)
        if only_active and hasattr(self.model, "active"):
            stmt = stmt.where(self.model.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True,
        order_by: Optional[Any] = None,
    ) -> List[ModelType]:
        """Lista registros con paginación y ordenamiento opcional."""
        stmt = select(self.model)
        if only_active and hasattr(self.model, "active"):
            stmt = stmt.where(self.model.active == True)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, only_active: bool = True) -> int:
        """Cuenta el total de registros existentes."""
        pk_col = list(self.model.__table__.primary_key.columns)[0]
        stmt = select(func.count(pk_col))
        if only_active and hasattr(self.model, "active"):
            stmt = stmt.where(self.model.active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create(self, obj: ModelType) -> ModelType:
        """Inserta un nuevo registro en la sesión."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, db_obj: ModelType, update_data: Dict[str, Any]) -> ModelType:
        """Actualiza un objeto existente con un diccionario de campos."""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def logical_delete(self, db_obj: ModelType) -> ModelType:
        """Aplica borrado lógico cambiando el flag active a False."""
        if hasattr(db_obj, "active"):
            db_obj.active = False
            self.session.add(db_obj)
            await self.session.flush()
            await self.session.refresh(db_obj)
        return db_obj
