from typing import Callable, List
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException
from app.db.models.user import User
from app.dependencies.database import get_db
from app.services.auth_service import AuthService

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependencia de FastAPI para obtener el usuario clínico autenticado desde Supabase Auth.
    Verifica el token JWT y recupera el perfil interno con su rol.
    """
    if not credentials or not credentials.credentials:
        raise AuthenticationException("Cabecera de autorización Bearer ausente o mal formada.")

    token = credentials.credentials
    auth_service = AuthService(session)
    user = await auth_service.authenticate_token(token)
    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Fábrica de dependencias que restringe el acceso de un endpoint a uno o más roles específicos.
    Ejemplo de uso: `current_user: User = Depends(require_roles(["admin", "professional"]))`
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ) -> User:
        auth_service = AuthService(session)
        auth_service.authorize_roles(current_user, allowed_roles)
        return current_user

    return role_checker


# Dependencias convenientes para roles comunes
require_admin = require_roles(["admin"])
require_professional_or_admin = require_roles(["admin", "professional"])
