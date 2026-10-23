import logging
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import verify_supabase_token
from app.db.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("lingua.auth")


class AuthService:
    """
    Servicio de autenticación y autorización clínica.
    Verifica los JWT emitidos por Supabase Auth, vincula la identidad con el perfil interno
    y aplica autorización basada en roles (RBAC).
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def authenticate_token(self, token: str) -> User:
        """
        Valida el JWT de Supabase Auth y recupera el usuario correspondiente en la base de datos.
        Si el usuario existe en Supabase pero aún no en el esquema interno, o si se trata de
        un usuario activo, resuelve el perfil y su rol.
        """
        payload = verify_supabase_token(token)
        user_uuid_str = payload.get("sub")
        try:
            user_id = uuid.UUID(user_uuid_str)
        except (ValueError, TypeError):
            raise AuthenticationException("Identificador de usuario inválido en el token de autenticación.")

        user = await self.user_repo.get_by_id_with_role(user_id)
        if not user:
            # Buscar por email en caso de que coincida con usuario registrado
            email = payload.get("email")
            if email:
                user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning("Usuario autenticado en Supabase con UUID %s no encontrado en perfil interno.", user_id)
            raise AuthenticationException(
                "Usuario autenticado pero sin perfil clínico registrado en el sistema. Contacte al administrador."
            )

        if not user.active:
            logger.warning("Intento de acceso por usuario inactivo/desactivado: %s", user.email)
            raise AuthorizationException("La cuenta de usuario se encuentra inactiva o deshabilitada.")

        return user

    def authorize_roles(self, user: User, allowed_roles: List[str]) -> None:
        """
        Valida que el rol asignado al usuario pertenezca a la lista de roles autorizados.
        No confía en roles enviados por el cliente frontend.
        """
        if not user.role or not user.role.active:
            raise AuthorizationException("El usuario no tiene un rol activo asignado.")

        user_role_name = user.role.name.lower().strip()
        allowed = [r.lower().strip() for r in allowed_roles]

        if user_role_name not in allowed:
            logger.warning(
                "Acceso denegado: Usuario %s con rol '%s' intentó acción restringida a %s.",
                user.email,
                user_role_name,
                allowed,
            )
            raise AuthorizationException(
                f"Permiso denegado. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}."
            )
