import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role
from app.db.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repositorio para la gestión de usuarios y roles clínicos."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id_with_role(self, user_id: uuid.UUID) -> Optional[User]:
        """Obtiene un usuario cargando ansiosamente su rol asociado."""
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.user_id == user_id, User.active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Busca un usuario por su correo electrónico."""
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email.lower().strip(), User.active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su nombre de usuario."""
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.username == username.strip(), User.active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Obtiene un rol por su nombre canónico (ej. 'admin', 'professional')."""
        stmt = select(Role).where(Role.name == name.lower().strip(), Role.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()
